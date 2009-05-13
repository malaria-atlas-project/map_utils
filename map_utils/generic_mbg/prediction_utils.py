import pymc as pm
import tables as tb
import numpy as np
from map_utils import asc_to_ndarray, get_header, exportAscii
from scipy import ndimage, mgrid
from histogram_utils import *
import time
import os

__all__ = ['grid_convert','mean_reduce','var_reduce','invlogit','hdf5_to_samps','vec_to_asc','asc_to_locs',
            'display_asc','display_datapoints','histogram_reduce','histogram_finalize','maybe_convert','sample_reduce',
            'sample_finalize']

def thread_partition_array(x):
    "Partition work arrays for multithreaded addition and multiplication"
    n_threads = int(os.environ['OMP_NUM_THREADS'])
    if len(x.shape)>1:
        maxind = x.shape[1]
    else:
        maxind = x.shape[0]
    bounds = np.array(np.linspace(0, maxind, n_threads+1),dtype='int')
    cmin = bounds[:-1]
    cmax = bounds[1:]
    return cmin,cmax

def invlogit(x):
    """A shape-preserving, in-place, threaded inverse logit function."""
    if not x.flags['F_CONTIGUOUS']:
        raise ValueError, 'x is not Fortran-contiguous'
    cmin, cmax = thread_partition_array(x)        
    pm.map_noreturn(iinvlogit, [(x,cmin[i],cmax[i]) for i in xrange(len(cmax))])
    return x

def fast_inplace_square(a):
    cmin, cmax = thread_partition_array(a)
    pm.map_noreturn(iasq, [(a,cmin[i],cmax[i]) for i in xrange(len(cmax))])
    return a

def maybe_convert(ra, field, dtype):
    """
    Tries to cast given field of given record array to given dtype. 
    Raises helpful error on failure.
    """
    arr = ra[field]
    try:
        return arr.astype(dtype)
    except:
        for i in xrange(len(arr)):
            try:
                np.array(arr[i],dtype=dtype)
            except:
                raise ValueError, 'Input column %s, element %i (starting from zero) is %s,\n which cannot be cast to %s'%(field,i,arr[i],dtype)

def validate_format_str(st):
    for i in [0,2]:
        if not st[i] in ['x','y']:
            raise ValueError, 'Directions must be x or y'
    for j in [1,3]:
        if not st[j] in ['-', '+']:
            raise ValueError, 'Orders must be + or -'
            
    if st[0]==st[2]:
        raise ValueError, 'Directions must be different'
    
    
def grid_convert(g, frm, to, validate=False):
    """Converts a grid to a new layout.
      - g : 2d array
      - frm : format string
      - to : format string
      
      Example format strings:
        - x+y+ (the way Anand does it) means that 
            - g[i+1,j] is west of g[i,j]
            - g[i,j+1] is north of g[i,j]
        - y-x+ (map view) means that 
            - g[i+1,j] is south of g[i,j]
            - g[i,j+1] is west of g[i,j]"""
    
    # Validate format strings
    if validate:
        for st in [frm, to]:
            validate_format_str(st)
        
    # Transpose if necessary
    if not frm[0]==to[0]:
        g = g.T
                
    first_dir = to[1]
    if not first_dir == frm[frm.find(to[0])+1]:
        g=g[::-1,:]
        
    sec_dir = to[3]
    if not sec_dir == frm[frm.find(to[2])+1]:
        g=g[:,::-1]
        
    # print first_dir, sec_dir
    return g

def buffer(arr, n=5):
    """Creates an n-pixel buffer in all directions."""
    out = arr.copy()
    if n==0:
        return out
    for i in xrange(1,n+1):
        out[i:,:] += arr[:-i,:]
        out[:-i,:] += arr[i:,:]
        out[:,i:] += arr[:,:-i]
        out[:,:-i] += arr[:,i:]
    return out

def asc_to_locs(fname, path='', thin=1, bufsize=1):
    """Converts an ascii grid to a list of locations where prediction is desired."""
    lon,lat,data = asc_to_ndarray(fname,path)
    data = grid_convert(data,'y-x+','x+y+')
    unmasked = buffer(True-data[::thin,::thin].mask, n=bufsize)
    
    # unmasked = None
    lat,lon = [dir[unmasked] for dir in np.meshgrid(lat[::thin],lon[::thin])]
    # lon,lat = [dir.ravel() for dir in np.meshgrid(lon[::thin],lat[::thin])]
    return np.vstack((lon,lat)).T*np.pi/180., unmasked
    
def display_asc(fname, path='', radians=True, *args, **kwargs):
    """Displays an ascii file as a pylab image."""
    from pylab import imshow
    lon,lat,data = asc_to_ndarray(fname,path)
    if radians:
        lon *= np.pi/180.
        lat *= np.pi/180.
    imshow(grid_convert(data,'y-x+','y+x+'),extent=[lon.min(),lon.max(),lat.min(),lat.max()],*args,**kwargs)
    
def display_datapoints(h5file, path='', cmap=None, *args, **kwargs):
    """Adds as hdf5 archive's logp-mesh to an image."""
    hf = tb.openFile(path+h5file)
    lpm = hf.root.metadata.logp_mesh[:]
    hf.close()
    from pylab import plot
    if cmap is None:
        plot(lpm[:,0],lpm[:,1],*args,**kwargs)
        
def mean_reduce(sofar, next):
    """A function to be used with hdf5_to_samps"""
    if sofar is None:
        return next
    else:
        return sofar + next
        
def var_reduce(sofar, next):
    """A function to be used with hdf5_to_samps"""
    if sofar is None:
        return next**2
    else:
        return sofar + next**2
        
def moments_finalize(prod, n):
    """Finalizes accumulated moments in human-interpreted surfaces."""
    mean = prod[mean_reduce] / n
    var = prod[var_reduce] / n - mean**2
    std = np.sqrt(var)
    std_to_mean = std/mean
    out = {'mean': mean, 'var': var, 'std': std, 'std-to-mean':std_to_mean}
    return out
        
def sample_reduce(sofar, next):
    """A function to be used with hdf5_to_samps. Keeps all samples with no data loss."""
    if sofar is None:
        return [next]
    else:
        sofar.append(next)
        return sofar
        
def sample_finalize(prod, n):
    """Converts accumulated samples to an array for output."""
    return np.array(prod[sample_reduce])

def histogram_reduce(bins, binfn):
    """Produces an accumulator to be used with hdf5_to_samps"""
    def hr(sofar, next):
        if sofar is None:
            sofar = np.zeros(next.shape+(len(bins),), dtype=int, order='F')
        # Call to Fortran function multiinc
        ind = binfn(next)
        # print 'multiinc called, number is %i'%np.sum(sofar)
        multiinc(sofar,ind)
        # print 'Done, number is %i'%np.sum(sofar)
        # print
        return sofar
    return hr
        
def histogram_finalize(bins, q, hr):
    """Converts accumulated histogram raster to desired quantiles"""
    def fin(products, n, bins=bins, q=q, hr=hr):
        out = {}
        hist = products[hr]
        # Call to Fortran function qextract
        quantile_surfs = qextract(hist,n,q,bins)
        for i in xrange(len(q)):
            out['quantile-%s'%q[i]] = quantile_surfs[i]
        # from IPython.Debugger import Pdb
        # Pdb(color_scheme='Linux').set_trace()   
        return out
    return fin


# TODO: Use predictive_mean_and_variance
def hdf5_to_samps(chain, metadata, x, burn, thin, total, fns, f_label, f_has_nugget, x_label, pred_cv_dict=None, nugget_label=None, postproc=None, finalize=None):
    """
    Parameters:
        chain : PyTables node
            The chain from which predictions should be made.
        x : array
            The lon, lat locations at which predictions are desired.
        burn : int
            Burnin iterations to discard.
        thin : int
            Number of iterations between ones that get used in the predictions.
        total : int
            Total number of iterations to use in thinning.
        fns : list of functions
            Each function should take four arguments: sofar, next, cols and i.
            Sofar may be None.
            The functions will be applied according to the reduce pattern.
        f_label : string
            The name of the hdf5 node containing f
        f_has_nugget : boolean
            Whether f is nuggeted.
        x_label : string
            The name of the hdf5 node containing the input mesh associated with f
            in the metadata.
        pred_cv_dict : dictionary
            {name : value on x}
        nugget_label : string (optional)
            The name of the hdf5 node giving the nugget variance
        postproc : function (optional)
            This function is applied to the realization before it is passed to
            the fns.
        finalize : function (optional)
            This function is applied to the products before returning. It should
            take a second argument which is the actual number of realizations
            produced.
    """
    
    cmin, cmax = thread_partition_array(x)
    
    products = dict(zip(fns, [None]*len(fns)))
    iter = np.arange(burn,len(chain.PyMCsamples),thin)
    n_per = total/len(iter)+1
    actual_total = n_per * len(iter)
    
    cols = chain.PyMCsamples.cols
    x_obs = getattr(metadata,x_label)[:]
    
    # Avoid memory errors
    max_chunksize = 1.e8 / x_obs.shape[0]
    n_chunks = int(x.shape[0]/max_chunksize+1)
    splits = np.array(np.linspace(0,x.shape[0],n_chunks+1)[1:-1],dtype='int')
    x_chunks = np.split(x,splits)
    i_chunks = np.split(np.arange(x.shape[0]), splits)
    
    M_pred = np.empty(x.shape[0])
    V_pred = np.empty(x.shape[0])
    
    time_count = -np.inf
    
    for k in xrange(len(iter)):
        
        i = iter[k]
        
        if time.time() - time_count > 10:
            time_count = time.time()
            print ((k*100)/len(iter)), '% complete'

        M_pred, S_pred = predictive_mean_and_std(chain, metadata, i, f_label, x_label, x, f_has_nugget, pred_cv_dict, nugget_label)
        
        # Postprocess if necessary: logit, etc.
        norms = np.random.normal(size=n_per)
        
        for j in xrange(n_per):
            surf = M_pred + S_pred * norms[j]
            # surf = M_pred.copy(order='F')
            # pm.map_noreturn(iaaxpy, [(surf, S_pred, norms[j], cmin[l], cmax[l]) for l in xrange(len(cmax))])
            # print  np.abs(surf-S_pred*norms[j]).max()
            if postproc is not None:
                surf = postproc(surf)
                        
            # Reduction step
            for f in fns:
                products[f] = f(products[f], surf)

    
    if finalize is not None:
        return finalize(products, actual_total)
    else:          
        return products
        
def normalize_for_mapcoords(arr, max):
    "Used to create inputs to ndimage.map_coordinates."
    arr /= arr.max()
    arr *= max
    
def vec_to_asc(vec, fname, out_fname, unmasked, path=''):
    """
    Converts a vector of outputs on a thin, unmasked, ravelled subset of an
    ascii grid to an ascii file matching the original grid.
    """
    header, f = get_header(fname,path)
    f.close()
    lon,lat,data = asc_to_ndarray(fname,path)
    data = grid_convert(data,'y-x+','x+y+')
    data_thin = np.empty(unmasked.shape)
    data_thin[unmasked] = vec
    
    mapgrid = np.array(mgrid[0:data.shape[0],0:data.shape[1]], dtype=float)
    normalize_for_mapcoords(mapgrid[0], data_thin.shape[0]-1)
    normalize_for_mapcoords(mapgrid[1], data_thin.shape[1]-1)
    
    if data_thin.shape == data.shape:
        out = data
    else:
        out = np.ma.masked_array(ndimage.map_coordinates(data_thin, mapgrid), mask=data.mask)
    
    # import pylab as pl
    # pl.close('all')
    # pl.figure()
    # pl.imshow(out, interpolation='nearest', vmin=0.)
    # pl.colorbar()
    # pl.title('Resampled')
    # 
    # pl.figure()
    # pl.imshow(np.ma.masked_array(data_thin, mask=True-unmasked), interpolation='nearest', vmin=0)
    # pl.colorbar()
    # pl.title('Original')
    
    out_conv = grid_convert(out,'x+y+','y-x+')
    
    header['NODATA_value'] = -9999
    exportAscii(out_conv.data,out_fname,header,True-out_conv.mask)
    
    return out
    

def predictive_mean_and_std(chain, meta, i, f_label, x_label, x, f_has_nugget=False, pred_cv_dict=None, nugget_label=None):
    """
    Computes marginal (pointwise) predictive mean and variance for f(x).
    Expects input from an hdf5 datafile.
        - chain : hdf5 group.
        - meta : hdf5 group.
        - i : integer.
        - f_label : string or array.
        - x : numpy array
        - pred_cv_dict : {name : value-on-predmesh}
        - nugget_label : string
    """

    if pred_cv_dict is not None:
        n = pred_cv_dict.keys()

        covariate_dict = meta.covariates[0]
        prior_covariate_variance = np.diag([covariate_dict[key][1] for key in n])

        pred_covariate_values = np.array([pred_cv_dict[key] for key in n])
        input_covariate_values = np.array([covariate_dict[key][0] for key in n])

    # How many times must a man condition a multivariate normal
    M = chain.group0.M[i]
    C = chain.group0.C[i]

    logp_mesh = getattr(meta,x_label)[:]    
    M_input = M(logp_mesh)
    M_pred = M(x)

    C_input = C(logp_mesh, logp_mesh)
    if pred_cv_dict is not None:
        C_input += np.dot(np.dot(input_covariate_values.T, prior_covariate_variance), input_covariate_values)
    if nugget_label is not None and f_has_nugget:
        nug = chain.PyMCsamples.cols.V[i]
        C_input += nug*np.eye(np.sum(logp_mesh.shape[:-1]))
    S_input = np.linalg.cholesky(C_input)
    

    C_cross = C(logp_mesh, x) 

    import warnings
    warnings.warn('Computing diagonal C(x) as amp**2! Remind Anand to change this if your covariance is nonstationary.')
    # V_pred = C(x)
    V_pred = C.params['amp']**2

    if pred_cv_dict is not None:
        C_cross += np.dot(np.dot(input_covariate_values.T, prior_covariate_variance), pred_covariate_values)
        V_pred = V_pred + np.sum(np.dot(np.sqrt(prior_covariate_variance), pred_covariate_values)**2, axis=0)
    if np.any(np.isnan(V_pred)):
        raise ValueError

    SC_cross = pm.gp.trisolve(S_input,C_cross,uplo='L',inplace=True)
    
    for mat in S_input, C_cross, SC_cross:
        if not mat.flags['F_CONTIGUOUS']:
            raise ValueError, 'Matrix is not Fortran-contiguous, fix the covariance function.'

    scc = np.asarray(SC_cross)
    fast_inplace_square(scc)
    V_out = V_pred - np.sum(scc,axis=0)

    try:
        f = chain.PyMCsamples.col(f_label)[i]
    except:
        f = getattr(meta,f_label)[:]

    M_out = M_pred + np.asarray(np.dot(SC_cross.T,pm.gp.trisolve(S_input, (f-M_input), uplo='L'))).squeeze()

    # from IPython.Debugger import Pdb
    # Pdb(color_scheme='Linux').set_trace()   
    if np.any(np.isnan(np.sqrt(V_out))) or np.any(np.isnan(M_out)):
        raise ValueError, 'Some predictive samples were NaN. Keep all your input files and tell Anand.'

    return M_out, np.sqrt(V_out)
    
if __name__ == '__main__':
    from pylab import *
    import matplotlib
    x, unmasked = asc_to_locs('frame3_10k.asc.txt',thin=20, bufsize=3)    
    # matplotlib.interactive('False')
    # plot(x[:,0],x[:,1],'k.',markersize=1)
    # show()
    hf = tb.openFile('ibd_loc_all_030509.csv.hdf5')
    ch = hf.root.chain0
    meta=hf.root.metadata
    
    def finalize(prod, n):
        mean = prod[mean_reduce] / n
        var = prod[var_reduce] / n - mean**2
        std = np.sqrt(var)
        std_to_mean = std/mean
        return {'mean': mean, 'var': var, 'std': std, 'std-to-mean':std_to_mean}
    
    products = hdf5_to_samps(ch,meta,x,1000,400,5000,[mean_reduce, var_reduce], 'V', invlogit, finalize)

    mean_surf = vec_to_asc(products['mean'],'frame3_10k.asc.txt','ihd-mean.asc',unmasked)
    std_surf = vec_to_asc(products['std-to-mean'],'frame3_10k.asc.txt','ihd-std-to-mean.asc',unmasked)