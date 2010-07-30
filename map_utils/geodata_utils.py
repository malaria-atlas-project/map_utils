from numpy import *
from numpy import ma
import numpy as np
import warnings

__all__ = ['display_surface', 'interp_geodata', 'cylindrical_area_correction', 'cylindrical_pixel_area', 'validate_format_str', 'grid_convert']

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
        # print 'First mismatch'
        g=g[::-1,:]

    sec_dir = to[3]
    if not sec_dir == frm[frm.find(to[2])+1]:
        # print 'Second mismatch'
        g=g[:,::-1]

    # print first_dir, sec_dir
    return g


def display_surface(lon, lat, data):
    """Displays CRU data on a map."""
    from mpl_toolkits import basemap
    m = Basemap(projection='cyl',
            llcrnrlon = lon.min(), 
            llcrnrlat = lat.min(),
            urcrnrlon = lon.max(),
            urcrnrlat = lat.max(),
            resolution = 'l')
    lon, lat = meshgrid(lon, lat)
    m.contourf(lon, lat, data, 30)
    
    return m
    
def cylindrical_area_correction(lon, lat):
    "For small pixels on a regular cylindrical grid, multiply the area by this."
    return cos(lat*pi/180.)
    
def cylindrical_pixel_area(llclon, llclat, urclon, urclat):
    "Returns the area of a pixel with given corners in km^2."
    return 6378.1**2*(sin(urclat*pi/180.)-sin(llclat*pi/180.))*(urclon-llclon)*pi/180.

def interp_geodata(lon_old, lat_old, data, lon_new, lat_new, mask=None, chunk=None, view='y-x+', order=1, nan_handler=None):
    """
    Takes gridded data, interpolates it to a non-grid point set.
    """
    from mpl_toolkits import basemap
    def chunker(v,i,chunk):
        return v[i*chunk:(i+1)*chunk]
        
    lat_argmins = np.array([np.argmin(np.abs(ln-lat_old)) for ln in lat_new])
    lon_argmins = np.array([np.argmin(np.abs(ln-lon_old)) for ln in lon_new])

    if view[0]=='y':
        lat_index = 0
        lon_index = 1
        lat_dir = int(view[1]+'1')
        lon_dir = int(view[3]+'1')
    else:
        lat_index = 1
        lon_index = 0
        lat_dir = int(view[3]+'1')
        lon_dir = int(view[1]+'1')

    N_new = len(lon_new)
    out_vals = zeros(N_new, dtype=float)

    if chunk is None:
        data = data[:]
        if mask is not None:
            data = ma.MaskedArray(data, mask)
        dconv = grid_convert(data,view,'y+x+')        
        for i in xrange(N_new):
            out_vals[i] = basemap.interp(dconv,lon_old,lat_old,lon_new[i:i+1],lat_new[i:i+1],order=order)
    
        if nan_handler is not None:
            where_nan = np.where(np.isnan(out_vals))
            out_vals[where_nan] = nan_handler(lon_old, lat_old, dconv, lon_new[where_nan], lat_new[where_nan], order)
    
        
    else:
        where_inlon = [np.where((lon_argmins>=ic*chunk[lon_index])*(lon_argmins<(ic+1)*chunk[lon_index]))[0] for ic in range(len(lon_old)/chunk[lon_index])]
        where_inlat = [np.where((lat_argmins>=jc*chunk[lat_index])*(lat_argmins<(jc+1)*chunk[lat_index]))[0] for jc in range(len(lat_old)/chunk[lat_index])]
        
        # Always iterate forward in longitude and latitude.
        for ic in range(data.shape[lon_index]/chunk[lon_index]):
            for jc in range(data.shape[lat_index]/chunk[lat_index]):

                # Who is in this chunk?
                where_inchunk = intersect1d(where_inlon[ic],where_inlat[jc])
                if len(where_inchunk) > 0:

                    # Which slice in latitude? 
                    if lat_dir == 1:
                        lat_slice = slice(jc*chunk[lat_index],(jc+1)*chunk[lat_index],None)
                    else:
                        lat_slice = slice(len(lat_old)-(jc+1)*chunk[lat_index],len(lat_old)-jc*chunk[lat_index],None)

                    # Which slice in longitude?
                    if lon_dir == 1:
                        lon_slice = slice(ic*chunk[lon_index],(ic+1)*chunk[lon_index],None)
                    else:
                        lon_slice = slice(len(lon_old)-(ic+1)*chunk[lon_index],len(lon_old)-ic*chunk[lon_index],None)

                    # Combine longitude and latitude slices in correct order
                    dslice = [None,None]
                    dslice[lat_index] = lat_slice
                    dslice[lon_index] = lon_slice
                    dslice = tuple(dslice)

                    dchunk = data[dslice]
                    if mask is not None:
                        mchunk = mask[dslice]
                        dchunk = ma.MaskedArray(dchunk, mchunk)

                    latchunk = chunker(lat_old,jc,chunk[lat_index])                
                    lonchunk = chunker(lon_old,ic,chunk[lon_index])

                    dchunk_conv = grid_convert(dchunk,view,'y+x+')

                    # for index in where_inchunk:
                    out_vals[where_inchunk] = basemap.interp(dchunk_conv, lonchunk, latchunk, lon_new[where_inchunk], lat_new[where_inchunk], order=order)
                    
                    if nan_handler is not None:
                        where_nan = np.where(np.isnan(out_vals[where_inchunk]))
                        out_vals[where_inchunk][where_nan] = nan_handler(lonchunk, latchunk, dchunk_conv, lon_new[where_inchunk][where_nan], lat_new[where_inchunk][where_nan], order)                

    return out_vals
                
        
