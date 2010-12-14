from zipfile import *
from numpy import *
from csv import reader

__all__ = ['str_to_val', 'RDC_info', 'RST_extract', 'CRU_extract', 'interp_CRU']

def str_to_val(str):

    if str.isspace():
        return None
    try:
        return int(str)
    except:
        pass
    try:
        return float(str)
    except:
        pass

    return str

def RDC_info(path,fname, zip=True):
    """Converts RST file to dictionary and returns it."""
    
    if zip:
        Z = ZipFile(path+'/'+fname+'.RDC.zip')
        info = Z.read(fname+'.RDC')

        fields = info.split('\r\n')
        field_dict = {}
        for field in fields:
            item = field.split(':')

            if len(item)==1:
                continue
        
            field_dict[item[0].rstrip(' ')] = str_to_val(item[1])
    else:
        field_dict = {}
        f = file(path+'/'+fname+'.rdc')
        for line in f:

            item = line.split(':')

            if len(item)==1:
                continue
        
            field_dict[item[0].rstrip(' ')] = str_to_val(item[1])
        f.close()
            
    return field_dict

def RST_extract(path, fname, zip=True, dtype=None):
    """Converts RST file to ndarray and returns it."""
    if zip:
        Z = ZipFile(path+'/'+fname+'.RDC.zip')
        data = Z.read(fname+'.rst')
        if dtype is None:
            return fromstring(data, dtype=float16)
        else:
            return fromstring(data, dtype=dtype)
    else:
        data = file(path+'/'+fname+'.rst')
        if dtype is None:
            out= fromfile(data, dtype=int16)
        else:
            out= fromfile(data, dtype=dtype)
        data.close()
        return out

def CRU_extract(path, fname, zip=True, dtype=None):
    """Converts RST and RDC file pair to long, lat, data tuple."""
    info = RDC_info(path, fname, zip)
    data = RST_extract(path, fname, zip, dtype)

    long = linspace(info['min. X'], info['max. X'], info['columns'])
    lat = linspace(info['min. Y'], info['max. Y'], info['rows'])

    # print data.shape, long.shape, lat.shape, info['rows'], info['columns']
    
    data = reshape(data, (info['rows'], info['columns']))

    return long, lat, data

def interp_CRU(path, fname, long_new, lat_new, zip=True, dtype=None):
    """
    Extracts from a CRU file, interpolates it to a non-grid point set.
    """
    from mpl_toolkits import basemap
    long_old, lat_old, data = CRU_extract(path, fname, zip, dtype)
    N_new = len(long_new)
    out_vals = zeros(N_new, dtype=float)

    for i in xrange(N_new):
        out_vals[i] = basemap.interp(data,long_old,lat_old,long_new[i],lat_new[i],order=1)
    return out_vals


