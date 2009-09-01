from numpy import *
from numpy import ma
from mpl_toolkits import basemap


__all__ = ['display_surface', 'interp_geodata', 'cylindrical_area_correction', 'cylindrical_pixel_area']

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

def interp_geodata(long_old, lat_old, data, long_new, lat_new, mask=None):
    """
    Takes gridded data, interpolates it to a non-grid point set.
    """
    
    print 'WARNING: interp_geodata may not be working properly. It gives results\
    that are different from those in the DB for urban and periurban.'

    N_new = len(long_new)
    out_vals = zeros(N_new, dtype=float)
    
    if mask is not None:
        data = ma.MaskedArray(data, mask)

    try:
        for i in xrange(N_new):
                        
            out_vals[i] = basemap.interp(data,long_old,lat_old,long_new[i],lat_new[i],order=1)
        return out_vals

    except KeyboardInterrupt:
        raise KeyboardInterrupt, 'Interrupted at datapoint %i of %i'%(i, N_new)
    
        