from __future__ import division
import numpy as np
import pylab as pl
import matplotlib
# from matplotlib.nxutils import points_inside_poly
from shapely import geometry, iterops, wkb, wkt
import shapely.geometry as geom
import pymc as pm
from csv import reader

__all__ = ['polygon_area', 'unit_to_grid', 'exclude_ues', 'plot_unit', 'obj_to_poly', 'NonSuckyShapefile','multipoly_sample',
            'sphere_poly_area','shapely_poly_area','shapely_multipoly_area']
    
# def inregion(x,y,r):
#     """
#     ins = inregion(x,y,r)
# 
#     Returns an array of booleans indicating whether the x,y pairs are
#     in region r. If region r contains multiple polygons, the ones inside 
#     the biggest one are assumed to be holes; the ones inside holes
#     are assumed to be islands; and so on.
# 
#     :Parameters:
#       x : array
#         x coordinates of test points
#       y : array
#         y coordinates of test points
#       r : ShapeObject
#         The region.
#     """
#     xy = np.vstack((x,y)).T
# 
#     # Record whether each point is inside each polygon.
#     ins = []
#     for v in r:
#         ins.append(points_inside_poly(xy,v))
#     ins = np.array(ins)
# 
#     # Return an array of booleans. An element is True if
#     # the corresponding point is inside an odd number of polygons.
#     return np.sum(ins, axis=0) % 2 == 1

# TODO: Debug and test the sampling ones    
# def land_sample(n):
#     """
#     Randomly-sampled points distributed over the earth's land.
#     Possibly use an even grid... Remember the Jacobian when 
#     taking integrals.
#     """
#     return multipoly_sample(n, land_multipoly)

def polygon_area(v):
    """
    Assumes 'v' is a counterclockwise array of (x,y) coordinates, with 
    the last equal to the first.
    
    Returns the area of the polygon they describe
    """
    x=v[:,0]
    y=v[:,1]
    out = -.5*np.sum(np.diff(x)*(y[:-1]+y[1:]))
    if out < 0:
        raise RuntimeError, 'Negative area. Are you sure your coordinates are counterclockwise?'
    return out    

def sphere_poly_area(v):
    """
    Assumes 'v' is a counterclockwise array of [lon,lat] tuples in radians, 
    with the last equal to the first. Returns the area of the polygon, on the 
    unit sphere.
    """
    x = v[:,0]
    y = np.sin(v[:,1])
    out = -.5*np.sum(np.diff(x)*(2.+y[:-1]+y[1:]))
    if out < 0:
        raise RuntimeError, 'Negative area. Are you sure your coordinates are counterclockwise?'
    return out
    
def shapely_poly_area(p):
    """
    Returns the area of the given shapely polygon in square kilometers.
    Treats the earth as a sphere.
    """
    exterior_coords = np.array(p.exterior.coords)*np.pi/180.
    interior_coords = [np.array(i.coords)*np.pi/180. for i in p.interiors]
    a = sphere_poly_area(exterior_coords[::-1]) - np.sum([sphere_poly_area(ic) for ic in interior_coords])
    return a*6378.1**2
    
def shapely_multipoly_area(m):
    """
    Returns the area of the given shapely multipolygon in square kilometers.
    Treats the earth as a sphere.
    """
    if isinstance(m, geometry.Polygon):
        return shapely_poly_area(m)
    else:
        return np.sum([shapely_poly_area(p) for p in m.geoms])

def multipoly_sample(n, mp):
    """
    Returns uniformly-distributed points on the earth's surface 
    conditioned to be inside a multipolygon.
    
    Not particularly fast.
    """

    # b = basemap.Basemap(-180,-90,180,90)
    
    if isinstance(mp, geometry.MultiPolygon):
        print 'Breaking down multipolygon'
        areas = [shapely_poly_area(p) for p in mp.geoms]
        areas = np.array(areas)/np.sum(areas)
        # ns = pm.rmultinomial(n, areas)
        stair = np.array(np.concatenate(([0],np.cumsum(areas*n))),dtype='int')
        ns = np.diff(stair)
        locs = [multipoly_sample(ns[i], mp.geoms[i]) for i in np.where(ns>0)[0]]
        return np.concatenate([loc[0] for loc in locs]), np.concatenate([loc[1] for loc in locs])
        
    
    lons = np.empty(n)
    lats = np.empty(n)
    
    done = 0
    
    xmin = mp.bounds[0]*np.pi/180
    ymin = mp.bounds[1]*np.pi/180
    xmax = mp.bounds[2]*np.pi/180
    ymax = mp.bounds[3]*np.pi/180
    
    print 'Starting: n=%i'%n
    while done < n:
        x = np.atleast_1d(pm.runiform(xmin,xmax, size=n))
        y = np.atleast_1d(np.arcsin(pm.runiform(np.sin(ymin),np.sin(ymax),size=n)))
        points=[geom.Point([x[i]*180./np.pi,y[i]*180./np.pi]) for i in xrange(len(x))]
        good = list(iterops.contains(mp, points, True))
        n_good = min(n,len(good))
        lons[done:done+n_good] = [p.coords[0][0] for p in good][:n-done]
        lats[done:done+n_good] = [p.coords[0][1] for p in good][:n-done]
        done += n_good
        print '\tDid %i, %i remaining.'%(n_good,n-done)
        
        # plot_unit(b,mp)
        # b.plot(x*180./np.pi,y*180./np.pi,'r.')
        # 
        # from IPython.Debugger import Pdb
        # Pdb(color_scheme='Linux').set_trace()   
    print 'Filled'
    return lons, lats

def unit_to_grid(unit, lon_min, lat_min, cellsize):
    """
    unit_to_grid(unit, lon_min, lat_min, cellsize)
    
    unit : a shapely polygon or multipolygon
    lon_min : The llc longitude of the master raster
    lat_min : The llc latitude of the master raster
    cellsize: of the master raster
    
    Retruns two arrays, lon and lat, of points on the raster in the unit.
    """
    llc = unit.bounds[:2]
    urc = unit.bounds[2:]
    
    lon_min_in = int((llc[0]-lon_min)/cellsize)
    lon_max_in = int((urc[0]-lon_min)/cellsize)+1
    lat_min_in = int((llc[1]-lat_min)/cellsize)
    lat_max_in = int((urc[1]-lat_min)/cellsize)+1  
    
    x_extent = np.arange(lon_min_in, lon_max_in+1)*cellsize + lon_min
    y_extent = np.arange(lat_min_in, lat_max_in+1)*cellsize + lat_min
    
    nx = len(x_extent)
    ny = len(y_extent)
    
    xm,ym = np.meshgrid(x_extent, y_extent)
    x=xm.ravel()
    y=ym.ravel()
    
    p=[geom.Point([x[i],y[i]]) for i in xrange(len(x))]
    
    return iterops.contains(unit, p, True)
    
def exclude_ues(xy, unit, ue_shapefile):
    """
    exclude_ues(xy,unit,ue_shapefile)
    
    xy : sequence of points.
    unit : The shapely polygon or multipolygon containing xy.
    ue_shapefile : A NonSuckyShapeFile object.
    
    Returns x and y filtered to be outside the polygons in the shapefile.
    """
    if not unit.is_valid:
        raise ValueError, 'invalid unit'
    intersect_fracs = []
    for ue in ue_shapefile:
        if unit.intersects(ue):
            xy = iterops.contains(unit, xy, True)
            intersect_fracs.append(unit.intersection(ue).area / ue.area)
        else:
            intersect_fracs.append(0)
    return xy, intersect_fracs

def plot_unit(b, unit, *args, **kwargs):
    """
    plot_unit(b, unit, *args, **kwargs)
    
    b : a Basemap.
    unit : a ShapeObject.
    args, kwargs : Passed to plot.
    """

    if isinstance(unit, geom.Polygon):
        v = np.array(unit.exterior)
        b.plot(v[:,0],v[:,1],*args, **kwargs)
    else:
        for subunit in unit.geoms:
            v = np.array(subunit.exterior)
            b.plot(v[:,0],v[:,1],*args, **kwargs)
    
        
def obj_to_poly(shape_obj, reverse=False):
    """
    Converts ShapeObject to shapely polygon or multipolygon
    """
    v = shape_obj.vertices()
    if len(v)==1:
        if reverse:
            return geom.Polygon(v[0][::-1])
        else:
            return geom.Polygon(v[0])
    else:
        if reverse:
            holes = []
            for g in v[1:]:
                holes.append(g[::-1])
            return geom.MultiPolygon([(v[0][::-1], holes)])
        return geom.MultiPolygon([(v[0], v[1:])])
    

class NonSuckyShapefile(object):
    """
    S = NonSuckyShapefile(fname)
    
    Holds some information about fname, and supports iteration and getiteming.
    Also has method plotall(b, *args, **kwargs).
    """
    def __init__(self, fname):
        from mpl_toolkits import basemap
        self.fname = fname
        self.sf = basemap.ShapeFile(fname)
        self.llc = self.sf.info()[2]
        self.urc = self.sf.info()[3]
        self.n = self.sf.info()[0]
        
        self.polygons = []
        for i in xrange(self.n):
            self.polygons.append(obj_to_poly(self.sf.read_object(i)))
            if not self.polygons[-1].is_valid:
                self.polygons[-1] = self.polygons[-1].buffer(0)
            if not self.polygons[-1].is_valid:
                self.polygons[-1] = obj_to_poly(self.sf.read_object(i), reverse=True)
            if not self.polygons[-1].is_valid:
                raise ValueError, 'Invalid polygon %i.'%i
        
        self.index = 0
        
    def __iter__(self):
        return self.polygons.__iter__()
    
    def __len__(self):
        return self.n
                
    def __getitem__(self, i):
        return self.polygons[i]
    
    def __array__(self):
        return np.array([el for el in self])
    
    def __getslice__(self, sl):
        return [self[i] for i in xrange(sl.start, sl.stop, sl.step)]
        
    def plotall(self, b, *args, **kwargs):
        matplotlib.interactive(False)
        for obj in self:
            plot_unit(b, obj, *args, **kwargs)            
        matplotlib.interactive(True)
