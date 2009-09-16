from numpy import *
from numpy import ma
from mpl_toolkits import basemap
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


def display_surface(long, lat, data):
    """Displays CRU data on a map."""

    m = Basemap(projection='cyl',
            llcrnrlon = long.min(), 
            llcrnrlat = lat.min(),
            urcrnrlon = long.max(),
            urcrnrlat = lat.max(),
            resolution = 'l')
    long, lat = meshgrid(long, lat)
    m.contourf(long, lat, data, 30)
    
    return m
    
def cylindrical_area_correction(lon, lat):
    "For small pixels on a regular cylindrical grid, multiply the area by this."
    return cos(lat*pi/180.)
    
def cylindrical_pixel_area(llclon, llclat, urclon, urclat):
    "Returns the area of a pixel with given corners in km^2."
    return 6378.1**2*(sin(urclat*pi/180.)-sin(llclat*pi/180.))*(urclon-llclon)*pi/180.

def interp_geodata(long_old, lat_old, data, long_new, lat_new, mask=None, chunk=None):
    """
    Takes gridded data, interpolates it to a non-grid point set.
    """
    
    print 'WARNING: interp_geodata may not be working properly. It gives results\
    that are different from those in the DB for urban and periurban.'
    
    def chunker(v,i,chunk):
        return v[i*chunk:(i+1)*chunk]
    
    def where_in(v1, v2, i, chunk):
        v1c = chunker(v1,i,chunk)
        return where((v2>=v1c[0])*(v2<v1c[-1]))
    
    where_inlon = [where_in(long_old, long_new, ic, chunk[0])[0] for ic in xrange(len(long_old)/chunk[1])]
    where_inlat = [where_in(lat_old, lat_new, jc, chunk[1])[0] for jc in xrange(len(lat_old)/chunk[0])]

    N_new = len(long_new)
    out_vals = zeros(N_new, dtype=float)
    
    if mask is not None:
        data = ma.MaskedArray(data, mask)

    if chunk is None:
        for i in xrange(N_new):
            out_vals[i] = basemap.interp(data,long_old,lat_old,long_new[i],lat_new[i],order=1)

    else:
        for ic in xrange(data.shape[0]/chunk[0]):
            for jc in xrange(data.shape[1]/chunk[1]):
                where_inchunk = intersect1d(where_inlat[ic],where_inlon[jc])
                if hasattr(data.attrs,'view'):
                    view = data.attrs.view
                else:
                    warnings.warn("Assuming map-view for %s because key 'view' not found in its data array's attrs."%data._v_file.filename)
                    view = 'y-x+'
                dchunk = data[ic*chunk[0]:(ic+1)*chunk[0],jc*chunk[1]:(jc+1)*chunk[1]]
                latchunk = chunker(lat_old,jc,chunk[0])                
                lonchunk = chunker(long_old,ic,chunk[1])
                for index in where_inchunk:
                    out_vals[index] = basemap.interp(grid_convert(dchunk,view,'y+x+'), lonchunk, latchunk, long_new[index], lat_new[index], order=1)
                    
    return out_vals
                
        