from __future__ import division
import numpy as np
from mpl_toolkits import basemap
import matplotlib.pyplot as pl
import matplotlib
from shapely import geometry, iterops, wkb, wkt
import shapely.geometry as geom
from csv import reader

def polygon_area(v):
    """
    polygon_area(v)
    Returns area of polygon
    """
    v_first = v[:-1][:,[1,0]]
    v_second = v[1:]
    return np.diff(v_first*v_second).sum()/2.0

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
        
        self.fname = fname
        self.sf = basemap.ShapeFile(fname)
        self.llc = self.sf.info()[2]
        self.urc = self.sf.info()[3]
        self.n = self.sf.info()[0]
        
        self.polygons = []
        for i in xrange(self.n):
            self.polygons.append(obj_to_poly(self.sf.read_object(i)))
            if not self.polygons[-1].is_valid:
                self.polygons[-1] = obj_to_poly(self.sf.read_object(i), reverse=True)
            if not self.polygons[-1].is_valid:
                raise ValueError, 'Invalid polygon %i. What the hell are you trying to pull?'%i
        
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
