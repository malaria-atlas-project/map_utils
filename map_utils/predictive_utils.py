import pymc as pm
import tables as tb
import numpy as np
from exportAscii import asc_to_ndarray, get_header, exportAscii
from scipy import ndimage, mgrid

__all__ = ['grid_convert','mean_reduce','var_reduce','invlogit','hdf5_to_samps','vec_to_asc','asc_to_locs']

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
    for i in xrange(1,n+1):
        out[i:,:] += arr[:-i,:]
        out[:-i,:] += arr[i:,:]
        out[:,i:] += arr[:,:-i]
        out[:,:-i] += arr[:,i:]
    return out

def asc_to_locs(fname, path='./', thin=1, bufsize=1):
    """Converts an ascii grid to a list of locations where prediction is desired."""
    lon,lat,data = asc_to_ndarray(fname,path)
    data = grid_convert(data,'y-x+','x+y+')
    unmasked = buffer(True-data[::thin,::thin].mask, n=bufsize)
    
    # unmasked = None
    lat,lon = [dir[unmasked] for dir in np.meshgrid(lat[::thin],lon[::thin])]
    # lon,lat = [dir.ravel() for dir in np.meshgrid(lon[::thin],lat[::thin])]
    return np.vstack((lon,lat)).T*np.pi/180., unmasked
        
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

def invlogit(x):
    """A shape-preserving version of PyMC's invlogit."""
    return pm.invlogit(x.ravel()).reshape(x.shape)

def hdf5_to_samps(chain, metadata, x, burn, thin, total, fns, nugname=None, postproc=None, finalize=None):
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
        nugname : string (optional)
            The name of the hdf5 node giving the nugget variance
        postproc : function (optional)
            This function is applied to the realization before it is passed to
            the fns.
        finalize : function (optional)
            This function is applied to the products before returning. It should
            take a second argument which is the actual number of realizations
            produced.
        """
    products = dict(zip(fns, [None]*len(fns)))
    iter = np.arange(burn,len(chain.PyMCsamples),thin)
    n_per = total/len(iter)+1
    actual_total = n_per * len(iter)
    
    cols = chain.PyMCsamples.cols
    f = cols.f
    M = chain.group0.M
    C = chain.group0.C
    x_obs = metadata.logp_mesh[:]
    
    for i in iter:
        print i
        
        # Observe M and C
        f = cols.f[i]
        M = chain.group0.M[i]
        C = chain.group0.C[i]
        pm.gp.observe(M,C,x_obs,f)
        
        # Mean and covariance of process
        M_pred = M(x)
        V_pred = C(x)
        if nugname is not None:
            V_pred += getattr(cols, nugname)[i]
        S_pred = np.sqrt(V_pred)
            
        # Postprocess if necessary: logit, etc.
        for j in xrange(n_per):
            surf = np.random.normal(loc=M_pred, scale=S_pred)
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
    
def vec_to_asc(vec, fname, out_fname, unmasked, path='./'):
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
    