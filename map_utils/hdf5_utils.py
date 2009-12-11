from tables import *
from numpy import *
from geodata_utils import *
from zipped_cru import RST_extract, RDC_info
import os
import numpy as np
import warnings

__all__ = ['table_to_recarray', 'hdf5_to_recarray', 'recarray_to_hdf5', 'hdf5_all_data', 'asc_to_hdf5', 'CRU_to_hdf5', 'interp_hdf5', 'windowed_extraction','bilinear_resample_hdf5']

def normalize_for_mapcoords(arr, fro, to):
    "Used to create inputs to ndimage.map_coordinates."
    
    arr /= arr.max()
    
    lenfro = len(fro)
    
    min_index = (to.min()-fro.min())/(fro.max()-fro.min())*lenfro
    max_index = (to.max()-fro.min())/(fro.max()-fro.min())*lenfro

    arr *= (max_index - min_index)
    arr += min_index
    
def box(orig, resamp):
    ind = np.array([np.argmin(np.abs(x-orig)) for x in resamp])
    lobound_ind = ind.copy()
    upbound_ind = ind.copy()+1

    where_below = np.where(orig[ind]>resamp)
    lobound_ind[where_below] = ind[where_below]-1
    upbound_ind[where_below] = ind[where_below]
    dx = (resamp - orig[lobound_ind])/(orig[1]-orig[0])
    return lobound_ind, upbound_ind, dx

def lon_and_lat(hfroot):
    if hasattr(hfroot,'lon'):
        lon = hfroot.lon[:]
    else:
        lon = hfroot.long[:]
    return lon, hfroot.lat[:]


def bilinear_resample_hdf5(hfroot, lon, lat):
    """
    Approximately evaluates a data layer stored in an hdf5 archive on the grid defined
    by lon and lat.
    
    hfroot must have attributes data, lon and lat. hfroot.data.attrs.view should be 
    a view string, eg 'y-x+'.
    """
    if hasattr(hfroot.data.attrs,'view'):
        view = hfroot.data.attrs.view
    else:
        warnings.warn("File %s's data does not have 'view' attr, assuming map view."%hfroot._v_file.filename)
        view = 'y-x+'
            
    this_lon, this_lat = lon_and_lat(hfroot)
    # Get lower- and upper-bound indices, and distances from nearest points.
    lon_li, lon_ui, lon_dx = box(this_lon, lon)
    lat_li, lat_ui, lat_dx = box(this_lat, lat)        
    if view[0]=='y':
        inner_li, inner_ui, inner_dx = lat_li, lat_ui, lat_dx
        outer_li, outer_ui, outer_dx = lon_li, lon_ui, lon_dx
    else:
        inner_li, inner_ui, inner_dx = lon_li, lon_ui, lon_dx
        outer_li, outer_ui, outer_dx = lat_li, lat_ui, lat_dx
    inner_dir=int(view[1]+'1')            
    outer_dir=int(view[3]+'1')

    # Get the weights, corner data and corner masks.
    wts = np.empty((2,2),dtype='object')
    r_ = np.empty((2,2), dtype='object')
    mask_ = np.empty((2,2), dtype='object')
    for k, inner in enumerate((inner_li, inner_ui)):
        for l,outer in enumerate((outer_li, outer_ui)):
            r_[k,l] = np.array([hfroot.data[j][outer[::outer_dir]] for j in inner[::inner_dir]])
            if hasattr(hfroot,'mask'):
                mask_[k,l] = np.array([hfroot.mask[j][outer[::outer_dir]] for j in inner[::inner_dir]])
            else:
                mask_[k,l] = 0.*r_[k,l]
            wts[k,l] = np.outer(inner_dx**k*(1-inner_dx)**(1-k), outer_dx**l*(1-outer_dx)**(1-l)) * (1-mask_[k,l])
                
    # Bilinear interpolation
    r = r_[0,0]*wts[0,0]+r_[0,1]*wts[0,1]+r_[1,0]*wts[1,0]+r_[1,1]*wts[1,1]

    # Account for masking: don't count the masked corner pixels.
    # If all the corner pixels are masked, mask the extracted pixel.
    if hasattr(hfroot,'mask'):
        normfac = wts[0,0]+wts[0,1]+wts[1,0]+wts[1,1]
        r[np.where(normfac>0)] /= normfac[np.where(normfac>0)]
        r = np.ma.masked_array(r, mask = normfac==0)    
    
    if view[0]=='y':
        r=r.T
    return r

def reconcile_multiple_rasters(hfroots, thin=1):
    """
    Resamples all rasters on the coarsest mesh, restricted to the smallest window.
    Returns the shared lon and lat vectors and a list of resampled data arrays.
    
    All rasters are returned in x+y+ view.
    """

    # Find the limits and coarseness.
    lon, lat = lon_and_lat(hfroots[0])
    lims = [lon.min(), lon.max(), lat.min(), lat.max()]
    dl = lon[1]-lon[0]
    coarsest = 0

    for i in xrange(1,len(hfroots)):
        lon, lat = lon_and_lat(hfroots[i])
        lims = [max(lims[0], lon.min()), min(lims[1], lon.max()), max(lims[2], lat.min()), min(lims[3], lat.max())]
        if lon[1]-lon[0]>dl:
            coarsest = i
            dl = lon[1]-lon[0]

    lon, lat = lon_and_lat(hfroots[coarsest])
    lon = lon[np.where((lon>=lims[0])*(lon<=lims[1]))][::thin]
    lat = lat[np.where((lat>=lims[2])*(lat<=lims[3]))][::thin]

    # Resample within limits, at coarseness.
    out = []
    for hfroot in hfroots:
        print "Resampling file %s."%hfroot._v_file.filename
        
        out.append(bilinear_resample_hdf5(hfroot, lon, lat))
    
    return lon,lat,out
__all__ += ['reconcile_multiple_rasters']

# Metadata: nrows, ncols, missing, minx, maxx, miny, maxy
def table_to_recarray(h5table):
    names = []
    arrays = []
    for name in h5table.colnames:
        names.append(name)
        arrays.append(h5table.col(name)[:].ravel())
    return rec.fromarrays(arrays, names=','.join(names))
    
def hdf5_to_recarray(h5group):
    names = []
    arrays = []
    for node in h5group:
        names.append(node.name)
        arrays.append(node[:].ravel())
    return rec.fromarrays(arrays,names=','.join(names))    
    
def recarray_to_hdf5(recarray, fname):
    h5file = openFile(fname, 'w')
    for name in recarray.dtype.names:
        h5file.createArray('/',name,recarray[name])
    h5file.close()

def hdf5_all_data(base='/usr/lib/python2.5/site-packages/MAPdata'):
    """
    Walks the directory tree and puts all datafiles into hdf archives, 
    if they aren't already in there.
    """
    for dirname, dirs, fnames in os.walk(base):

        os.chdir(dirname)

        for fname in fnames:
        
            if fname[-4:]=='.asc':
                if not fname[:-4] + '.hdf5' in fnames:
                    print 'asc:', dirname+'/'+fname
                    q = asc_to_hdf5(fname, dirname+'/')
                            
            if fname[-8:] == '.rst.zip':
                if not fname[:-8]+'.hdf5' in fnames:
                    print 'cru:', dirname+'/'+fname
                    q = CRU_to_hdf5(fname[:-8], dirname+'/')
                
def asc_to_hdf5(fname, path='./'):
    """
    Extracts long, lat, data from an ascii-format file.
    """
    f = file(path+fname,'r')
    
    # Extract metadata from asc file.
    ncols = int(f.readline()[14:])
    nrows = int(f.readline()[14:])
    xllcorner = float(f.readline()[14:])
    yllcorner = float(f.readline()[14:])
    cellsize = float(f.readline()[14:])
    NODATA_value = int(f.readline()[14:])
    
    # Make longitude and latitude vectors.    
    long = xllcorner + arange(ncols) * cellsize
    lat = yllcorner + arange(nrows) * cellsize
    
    # Initialize hdf5 archive.
    h5file = openFile(path+fname[:-4]+'.hdf5', mode='w', title=fname[:-4] + ' in hdf5 format')

    # Write hdf5 archive metadata.
    h5file.root._v_attrs.asc_file = path + fname
    h5file.root._v_attrs.ncols = ncols
    h5file.root._v_attrs.nrows = nrows
    h5file.root._v_attrs.missing = NODATA_value
    h5file.root._v_attrs.minx = long.min()
    h5file.root._v_attrs.maxx = long.max()
    h5file.root._v_attrs.miny = lat.min()
    h5file.root._v_attrs.maxy = lat.max()
    
    # Add longitude and latitude to archive, uncompressed.
    h5file.createArray('/','long',long)
    h5file.createArray('/','lat',lat)
    
    # Add data to archive, heavily compressed, row-by-row (if a row won't fit in memory, the whole array won't fit on disk).
    h5file.createCArray('/', 'data', Float64Atom(), (nrows, ncols), filters = Filters(complevel=9, complib='zlib'))    
    data = h5file.root.data
    for i in xrange(nrows):
        data[-i-1,:] = fromstring(f.readline(), dtype=float, sep=' ')
    
    return h5file



def CRU_to_hdf5(fname, path='./'):
    """
    Converts RST and RDC file pair to an hdf5 archive.
    """
    # Extract info and data from CRU file into memory (would want to do this chunkwise eventually)
    info = RDC_info(path, fname)
    data = RST_extract(path, fname)

    # Make latitude and longitude vectors.
    long = linspace(info['min. X'], info['max. X'], info['columns'])
    lat = linspace(info['min. Y'], info['max. Y'], info['rows'])
    nrows = len(lat)
    ncols = len(long)

    # Initialize hdf5 archive.
    h5file = openFile(path+fname +'.hdf5', mode='w', title=fname[:-4] + ' in hdf5 format')
    
    # Write hdf5 archive's metadata.
    h5file.root._v_attrs.rst_file = path + fname + '.rst'
    h5file.root._v_attrs.RDC_file = path + fname + '.RDC'        
    h5file.root._v_attrs.minx = long.min()
    h5file.root._v_attrs.maxx = long.max()
    h5file.root._v_attrs.miny = lat.min()
    h5file.root._v_attrs.maxy = lat.max()
    h5file.root._v_attrs.nrows = nrows
    h5file.root._v_attrs.ncols = ncols
    h5file.root._v_attrs.missing = 0.
    
    # Write latitude and longitude vectors to hdf5 archive, uncompressed.
    h5file.createArray('/','long',long)
    h5file.createArray('/','lat',lat)
    
    # Write data to hdf5 archive, compressed.
    h5file.createCArray('/', 'data', Float64Atom(), (nrows, ncols), filters = Filters(complevel=9, complib='zlib'))    
    h5file.root.data[:,:] = reshape(data, (info['rows'], info['columns']))[::-1,:]

    return h5file


def make_contigs(arr):
    """
    Breaks increasing array arr into contiguous slices.
    Returns list of (start,stop) tuples
    """
    breaks = where(diff(arr)>1)[0]
    start = [0] + list(arr+1)
    end = list(arr+1) + [len(arr)]
    return zip(start, end)


def add_mask(path, fname, missing_codes):
    """
    Adds a 'mask' array to the hdf5 file.
    """
    h5file = openFile(path+fname+'.hdf5', mode='a')
    data = h5file.root.data

    try:
        h5file.createCArray('/', 'mask', BoolAtom(), data.shape, filters = Filters(complevel=9, complib='zlib'))    
    except NodeError:
        pass

    mask = h5file.root.mask
    try:
        for i in xrange(data.shape[0]):
            mask[i,:] = False
            this_d_row = data[i,:]
            this_m_row = mask[i,:]
            for code in missing_codes:
                this_m_row[where(this_d_row == code)] = True
            mask[i,:] = this_m_row
            
        h5file.close()
        
    except KeyboardInterrupt:
        raise KeyboardInterrupt, 'Interrupted at row %i of %i'%(i, data.shape[0])
        
    
def interp_hdf5(path, fname, long_new, lat_new, with_mask=True):
    """
    Interpolates layer in hdf5 archive to a non-grid point set.
    """
    h5file = openFile(path+fname+'.hdf5', mode='r')
    lat_old, data = h5file.root.lat[:], h5file.root.data
    
    if hasattr(h5file.root,'long'):
        long_old = h5file.root.long[:]
    else:
        long_old = h5file.root.lon
    
    mask = None
    if with_mask:
        if hasattr(h5file.root, 'mask'):
            mask = h5file.root.mask
        
    return interp_geodata(long_old, lat_old, data, long_new, lat_new, mask)



def windowed_extraction(path, fname, long_new, lat_new, window_sizes=[3]):
    """
    Takes gridded data, and makes center-pixel and windowed
    mean and variance extractions.
    """
    
    # Read latitude, longitude, data, and missing data sybol out of archive.
    # Leave data compressed on disk, just get a reference to it.
    h5file = openFile(path+'/'+fname+'.hdf5', mode='r')
    lat_old, data, missing = h5file.root.lat[:], h5file.root.data, h5file.root._v_attrs.missing
    
    if hasattr(h5file.root,'long'):
        long_old = h5file.root.long[:]
    else:
        long_old = h5file.root.lon

    N_new = len(long_new)
    N_windows = len(window_sizes)

    # Initialize output arrays.
    out_mean = zeros((N_windows, N_new), dtype=float)
    out_var = zeros((N_windows, N_new), dtype=float)

    # Initialize work arrays.
    center_longs = zeros(N_new, dtype=int)
    center_lats = zeros(N_new, dtype=int)

    # Iterate over requested extractions.
    for j in xrange(len(window_sizes)):
        size = window_sizes[j]
        N_eachside = (size-1)/2

        # Iterate over centerpoints.
        for i in xrange(N_new):
            
            # Identify center pixel
            center_longs[i] = argmin(abs(long_old - long_new[i]))
            center_lats[i] = argmin(abs(lat_old - lat_new[i]))

            # Identify index pairs participating in window.
            indices = meshgrid( arange(center_longs[i] - N_eachside, center_longs[i] + N_eachside+1),
                                arange(center_lats[i] - N_eachside, center_lats[i] + N_eachside+1))
            indices_x = indices[0].ravel()
            indices_y = indices[1].ravel()
            
            # Trim the indices, leaving only the ones that are within the rectangle.
            good_indices = where((indices_x>=0) * (indices_y>=0) * (indices_x<len(long_old)) * (indices_y<len(lat_old)))
            indices_x = indices_x[good_indices]
            indices_y = indices_y[good_indices]         
            
            # Extract the data in the window points that are within the rectangle.
            data_in_window = zeros(len(indices_x),dtype=float)
            for k in xrange(len(indices_x)):
                data_in_window[k] = data[indices_y[k], indices_x[k]]

            # Trim the data again, keeping only observations that aren't missing.
            good_data_in_window = data_in_window[where(data_in_window!=missing)]
            
            # If there are any non-missing observations in the window, compute mean and variance.
            if len(good_data_in_window)>0:
                out_mean[j, i] = mean(good_data_in_window)
                if len(good_data_in_window)>1:
                    out_var[j, i] = var(good_data_in_window)
                else:
                    out_var[j,i] = 1
                
            # Otherwise write missing data symbol to mean and variance.
            else:
                out_mean[j,i] = missing
                out_var[j,i] = missing

    return out_mean, out_var

# from __init__ import MAPdata
# out = windowed_extraction('./', 'MARA', MAPdata['LONG'], MAPdata['LAT'], window_sizes=[3])