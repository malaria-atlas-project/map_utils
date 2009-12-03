import numpy as np
import string

__all__ = ['asc_to_ndarray','exportAscii', 'get_header', 'reexport_ascii','exportAscii2']

def get_header(fname, path='./'):
    """"
    Parses an ascii file's header to a dictionary.
    Returns it along with the rest of the file.
    """
    f = file(path+fname,'r')
    
    header = {}
    headlines = 0
    
    while True:
        line = f.readline()
        clean_line = string.strip(line).split()
        key = string.strip(clean_line[0])
        val = string.strip(clean_line[-1])
        if not key[0].isalpha():
            break
        try:
            val = int(val)
        except:
            val = float(val)
        if key != 'NODATA_value':
            key = key.lower()
        header[key] = val
        headlines += 1
    
    f.close()

    for key in ['ncols','nrows','cellsize','xllcorner','yllcorner']:
        if not header.has_key(key):
            raise KeyError, 'File %s header does not contain key %s'%(path+fname, key)
    
    return header, headlines
    

def asc_to_ndarray(fname, path='./'):
    """
    Extracts long, lat, data from an ascii-format file.
    Data is a masked array if the header contains NODATA_value
    """
    header, headlines = get_header(fname, path)
    f = file(path+fname,'r')
    
    for i in xrange(headlines):
        f.readline()    
    
    ncols = header['ncols']
    nrows = header['nrows']
    cellsize = header['cellsize']
    
    long = header['xllcorner'] + np.arange(ncols) * cellsize
    lat = header['yllcorner'] + np.arange(nrows) * cellsize
    data = np.zeros((nrows, ncols), dtype=float)
    for i in xrange(nrows):
        line = f.readline()
        data[i,:] = np.fromstring(line, dtype=float, sep=' ')
    # print data.shape, nrows, ncols
    f.close()
    
    if header.has_key('NODATA_value'):
        data = np.ma.masked_array(data, mask=data==header['NODATA_value'])
    
    return long, lat, data

def reexport_ascii(fname, path='./'):
    """
    Useful if, for example, the generated ascii file doesn't have 
    Windows returns.
    """
    header, headlines = get_header(fname, path)
    
    long, lat, data = asc_to_ndarray(fname, path)
    
    exportAscii(data.data, fname, header, True-data.mask)

def exportAscii (arr,filename,headerDict,mask=0):
    "Exports an array and a header to ascii"

    import numpy as np
    
    # create output file link
    f = file(filename,"w")
    
    # write in header
    f.write('ncols\t'+str(headerDict['ncols'])+'\r\n')
    f.write('nrows\t'+str(headerDict['nrows'])+'\r\n')
    f.write('xllcorner\t'+str(headerDict['xllcorner'])+'\r\n')
    f.write('yllcorner\t'+str(headerDict['yllcorner'])+'\r\n')
    f.write('cellsize\t'+str(headerDict['cellsize'])+'\r\n')
    f.write('NODATA_value\t'+str(headerDict['NODATA_value'])+'\r\n')
    
    # write in main array
    
    # optionally apply mask - specified by passing a mask array (0s and 1s) - 0s will be set to NODATA_value
    if type(mask)!=int:
        # perform check that the number of rows and columns is the same in both 1km grids    
        if (np.shape(mask) != np.shape(arr)):
            print 'WARNING!! mask supplied to exportAscii has wrong shape!! (mask = '+str(np.shape(mask))+' and array = '+str(np.shape(arr))+'): WILL NOT APPLY MASK!!'
        else:
            arr[mask==0]=headerDict['NODATA_value'] 

    for row in arr:
        row.tofile(f, sep=' ')
        f.write('\r\n')

    f.close()

def exportAscii2(lon,lat,data,filename):
    "Exports longitude and latitude vectors and a data array to ascii."
    if data.shape != (len(lat),len(lon)):
        raise ValueError, 'Data is wrong shape'

    data.fill_value=np.asscalar(np.array(-9999).astype(data.dtype))
    header = {'ncols': len(lon),
                'nrows': len(lat),
                'cellsize': lon[1]-lon[0],
                'xllcorner': lon.min(),
                'yllcorner': lat.min(),
                'NODATA_value': data.fill_value}
    exportAscii(data.filled(),filename,header,True-data.mask)
