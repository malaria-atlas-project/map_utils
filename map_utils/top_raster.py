import os
import tables as tb
import numpy as np
from map_utils import *

__all__ = ['import_raster', 'export_raster']

def import_raster(name,path,type=None):
    known_types = ['asc','hdf5','flt','RDC.zip','rdc']
    if type is None:
        for type in known_types:
            if name+'.'+type in os.listdir(path):
                return import_raster(name, path, type=type)
        raise OSError, 'No file named %s found in %s.'%(' or '.join([name+'.'+type for type in known_types]), path)
    elif type=='asc':
        lon,lat,data = asc_to_ndarray(name+'.asc',path=path)
    elif type=='hdf5':
        hf = tb.openFile(os.path.join(path,name+'.hdf5'))
        lon = hf.root.lon[:]
        lat = hf.root.lat[:]
        data = grid_convert(np.ma.masked_array(hf.root.data[:], mask=hf.root.mask[:]), hf.root.data.attrs.view, 'y-x+')
        hf.close()
    elif type=='flt':
        lon,lat,data = flt_to_ndarray(name, path=path)
    elif type=='rdc':
        lon,lat,data = CRU_extract(path, name, zip=False)
    elif type=='RDC.zip':
        lon,lat,data = CRU_extract(path, name, zip=True)
    return np.sort(lon),np.sort(lat),data,type
    
def export_raster(lon,lat,data,name,path,type,view='y-x+'):
    lon = np.sort(lon)
    lat = np.sort(lat)
    if type=='asc':
        exportAscii2(lon,lat,data,os.path.join(path,name+'.asc'),view)
    elif type=='hdf5':
        hf = tb.openFile(os.path.join(path,name+'.hdf5'),'w')
        hf.createArray('/','lon',lon)
        hf.createArray('/','lat',lat)
        hf.createCArray('/','data',shape=data.shape,atom=tb.FloatAtom(),filters=tb.Filters(complib='zlib',complevel=1))
        hf.createCArray('/','mask',shape=data.shape,atom=tb.BoolAtom(),filters=tb.Filters(complib='zlib',complevel=1))
        hf.root.data[:]=data.data
        hf.root.mask[:]=data.mask
        hf.root.data.attrs.view=view
        hf.close()
    elif type=='flt':
        export_flt(lon,lat,data,os.path.join(path,name),view)
    else:
        raise NotImplementedError, 'Do not know how to export raster type %s'%type