import tables as tb
import numpy as np
import os, sys
from zipfile import ZipFile
from modis_names import parse_filename, tfa_chans, lw_chans, convert

__all__ = ['extract_zipped_rst','mirror_as_hdf5']

class ZipReadError(Exception):
    pass

def split_all_exts(name):
    """
    Splits all extensions from multi-extension filenames.
    """
    b,e = os.path.splitext(name)
    if e=='':
        return b
    else:
        return split_all_exts(b)

def extract_zipped_rst(path, fname):
    """
    Extracts relevant stuff from a zipped RST file.
    """
    
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
    
    
    Z = ZipFile(path+'/'+fname+'.rst.zip')

    # Get rst header as dict
    info = Z.read(fname+'.rdc')
    fields = info.split('\r\n')
    info = {}
    for field in fields:
        item = field.split(':')

        if len(item)==1:
            continue
    
        info[item[0].rstrip(' ')] = str_to_val(item[1])
        
    # Figure out lon and lat arrays
    lon = np.linspace(info['min. X'], info['max. X'], info['columns'])
    lat = np.linspace(info['min. Y'], info['max. Y'], info['rows'])
    
    # Pull data out of rst, cast to float, postprocess
    try:
        data = Z.read(fname+'.rst')
    except:
        raise ZipReadError

    if len(data)==len(lat)*len(lon):
        dtype = np.dtype('uint8')
    elif len(data)==len(lat)*len(lon)*2:
        dtype=np.dtype('int16')
    else:
        raise ZipReadError, 'Raw data is not of a size consistent with unsigned 8-bit or signed 16-bit integers.'
        
    return lon, lat, data, dtype

def parse_file_and_dir(f, dirname):
    """
    Learns a file's kind based on its directory and filename, and parses it.
    """
    
    if dirname in tfa_chans:
        kind='tfa'
    elif dirname in lw_chans:
        kind='land-water'
    else:
        raise ValueError, 'Directory name %s is not a valid channel.'%dirname
        
    try:
        thiskind = kind
        if kind=='land-water':
            if f.find('mask')>-1:
                thiskind='land-water mask'
        return parse_filename(split_all_exts(f),kind=thiskind)

    except:
        cls, inst, tb = sys.exc_info()
        msg = """Error in %s file %s, original message:  """%(thiskind, f)+inst.message
        raise cls, cls(msg), tb

def gentle_mkdir(path):
    try:
        os.listdir(path)
    except OSError:
        os.mkdir(path)

def is_admissible_rst(f):
    # Want zipped RST archives, not 'info' or 'abs' files, with geographic projection.
    return f.find('rst')>-1 \
            and os.path.splitext(f)[1]=='.zip'\
            and f.find('info')==-1 \
            and f.find('abs')==-1
    
def tupproof_str(s):
    if isinstance(s, tuple):
        return str(s[0])+'-to-'+str(s[1])
    else:
        return s

def stream_to_hdf(hf, data, dtype, shape, conversion, memmax=1.e8):
    """
    Writes a data string into an hdf5 archive by chunks, saving memory.
    """
    
    # # Uncomment for really hard compression
    # hf.createCArray('/','data',tb.Float32Atom(),shape,filters=tb.Filters(complevel=9,complib='bzip2'))
    
    # Uncomment for minimal compression
    hf.createCArray('/','data',tb.Float32Atom(),shape,filters=tb.Filters(complevel=1))
    
    chunksize = np.int(memmax/shape[1]/8.)
    nchunks = np.int(shape[0]/chunksize)
    
    # Write in internal chunks
    for chunk in xrange(nchunks):
        minrow = chunk*chunksize
        maxrow = (chunk+1)*chunksize
        data_chunk = conversion(np.fromstring(data[minrow*shape[1]*dtype.itemsize:maxrow*shape[1]*dtype.itemsize], dtype=dtype))
        hf.root.data[minrow:maxrow,:] = data_chunk.reshape(-1,shape[1])
        hf.flush()
    
    # Write in last chunk
    minrow = nchunks*chunksize
    data_chunk = conversion(np.fromstring(data[minrow*shape[1]*dtype.itemsize:], dtype=dtype))
    hf.root.data[minrow:,:] = data_chunk.reshape(-1,shape[1])
        
    

def mirror_as_hdf5(frompath, topath):
    cwd = os.getcwd()
    
    failures = []
    
    # Walk file tree.
    for dirpath, dirnames, fnames in os.walk(frompath):

        # Make sure this directory contains MODIS data, not eg documentation.
        dirname = os.path.split(dirpath)[-1]
        if dirname in tfa_chans + lw_chans:
            new_dirpath = dirpath.replace(frompath,topath)
        else:
            continue

        # Create mirrored data directory.
        gentle_mkdir(new_dirpath)
        os.chdir(new_dirpath)
        
        # Iterate over the zipped RST files in geographic projection.
        for f in fnames:
            if is_admissible_rst(f):
                d = parse_file_and_dir(f, dirname)            

                labels = sorted(d.keys())
        
                readable_name = '.'.join([tupproof_str(d[key]).replace(' ','-') for key in labels])
            
                if d['projection'] == 'geographic':
                    print d
                    hf = tb.openFile('%s.hdf5'%readable_name,'w')
                    
                    # Read in rst file
                    print '\textracting'
                    try:
                        lon,lat,data,dtype = extract_zipped_rst(dirpath, f.replace('.rst.zip', ''))        
                    except ZipReadError:    
                        failures.append(os.path.join(dirpath,f))

                    # Write out hdf5
                    print '\tconverting and recompressing'
                    hf.createArray('/','lon',lon)
                    hf.createArray('/','lat',lat)

                    if d.has_key('channel'):
                        chan = d['channel']
                    else:
                        chan = None
                    product = d['product']
                    conversion = lambda x, chan=chan, product=product: convert(x, chan, product)

                    stream_to_hdf(hf, data, dtype, (len(lat), len(lon)), conversion)
                    hf.close()

                    print '\tdone, initial size %i, final size %i\n\n'%tuple([os.stat(n).st_size for n in (os.path.join(dirpath, f), readable_name + '.hdf5')])
            
    os.chdir(cwd)
    print 'Failures: %s'%failures
        
if __name__ == '__main__':
    mirror_as_hdf5('/srv/data/MODIS/global','/srv/data/MODIS-hdf5')