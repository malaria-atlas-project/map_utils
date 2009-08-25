from numpy import *
from numpy import ma
from mpl_toolkits import basemap


__all__ = ['display_surface', 'interp_geodata']

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
    
        