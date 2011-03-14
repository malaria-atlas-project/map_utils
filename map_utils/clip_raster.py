import numpy as np
import shapely
import map_utils

def get_closest_index(vec, val):
    return np.argmin(np.abs(vec-val))
    
def clip_vector(vec, minval, maxval):
    i_min,i_max= max(0,get_closest_index(vec, minval)-1), min(len(vec)-1,get_closest_index(vec,maxval)+1)+1
    return i_min, i_max, vec[i_min:i_max]

def isbetween(one,two,test):
    out = test==one
    out |= np.sign(np.maximum(one,two)-test) == np.sign(test-np.minimum(one,two))
    return out
    
def crr(rx, ry, rm, x, y):
    crossings = np.zeros((len(x),len(y)),dtype='int')

    xmn = x.min()
    xmx = x.max()
    dx = x[1]-x[0]

    where_vertical = np.where(np.isinf(rm))[0]
    if len(where_vertical)>0:
        rxv, ryv_u, ryv_l = rx[where_vertical], ry[where_vertical], ry[where_vertical+1]

    where_sensible = np.where((rm != 0) * ~np.isinf(rm))[0]
    if len(where_sensible)>0:
        rxs_l, rxs_u, rms, rys = rx[where_sensible], rx[where_sensible+1], rm[where_sensible], ry[where_sensible]
    
    for i, y_ in enumerate(y):
        # All the vertical crossings at this longitude.
        
        if len(where_vertical)>0:
            xc_vert = rxv[np.where(isbetween(ryv_u,ryv_l,y_))]    
        else:
            xc_vert = []
        
        if len(where_sensible)>0:
            xc_sens = rxs_l+(y_-rys)/rms                    
            xc_sens = xc_sens[np.where(isbetween(rxs_l,rxs_u,xc_sens))]
        else:
            xc_sens = []
        
        xc = np.hstack((xc_sens, xc_vert))
        xc = xc[np.where((xc>=xmn)*(xc<=xmx))]
            
        if len(xc)>0:
            for xc_ in xc:
                crossings[np.ceil((xc_-xmn)/dx):, i] += 1
    
    return crossings
            
def clip_raster_to_ring(ring, lon, lat, isin, hole=False):
    ring_slope = np.diff(ring.xy[1])/np.diff(ring.xy[0])
    llcx,llcy,urcx,urcy = ring.bounds
    
    llcx_i, urcx_i, lon_patch = clip_vector(lon, llcx, urcx)
    llcy_i, urcy_i, lat_patch = clip_vector(lat, llcy, urcy)
    
    # Assume here that view is x+y+.
    crossings = crr(np.array(ring.xy[0]),np.array(ring.xy[1]),np.array(ring_slope),lon_patch,lat_patch)
    isin_ring = (crossings%2==1)
        
    if hole:
        isin[llcx_i:urcx_i, llcy_i:urcy_i] &= ~isin_ring 
    else:
        isin[llcx_i:urcx_i, llcy_i:urcy_i] |= isin_ring 
    
def clip_raster_to_polygon(poly, lon, lat, isin):
    clip_raster_to_ring(poly.exterior, lon, lat, isin)
    for i in poly.interiors:
        clip_raster_to_ring(i, lon, lat, isin, hole=True)
    
def clip_raster(geom, lon, lat, view='y+x+'):
    """
    Returns an array in the desired view indicating which pixels in the
    meshgrid generated from lon and lat are inside geom.
    """    
    # Internal view is x+y+.
    isin = np.zeros((len(lon), len(lat)),dtype='bool')

    if isinstance(geom, shapely.geometry.multipolygon.MultiPolygon):
        geoms = geom.geoms
    else:
        geoms = [geom]
    for i,g in enumerate(geoms):
        clip_raster_to_polygon(g, lon, lat, isin)

    return map_utils.grid_convert(isin, 'x+y+', view)
    
# if __name__ == '__main__':
#     import pylab as pl    
#     import pickle, map_utils
#     canada = pickle.loads(file('Canada.pickle').read())
#     lon,lat,data,type = map_utils.import_raster('gr10_10k','.')
#     
#     p = canada#.geoms[5251]
#     
#     isin = clip_raster(p, lon, lat)
#     import pylab as pl
#     pl.clf()
#     pl.imshow(isin,extent=(lon.min(),lon.max(),lat.min(),lat.max()),interpolation='nearest')
#     # pl.imshow(isin,interpolation='nearest')
#     # for g in p.geoms:
#     # pl.plot(p.exterior.xy[0],g.exterior.xy[1],'r-')