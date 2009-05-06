import numpy as np
import string

__all__ = ['asc_to_ndarray','exportAscii', 'get_header']

def get_header(fname, path='./'):
    """"
    Parses an ascii file's header to a dictionary.
    Returns it along with the rest of the file.
    """
    f = file(path+fname,'r')
    
    header = {}
    
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
        header[key] = val
    

    for key in ['ncols','nrows','cellsize','xllcorner','yllcorner']:
        if not header.has_key(key):
            raise KeyError, 'File %s header does not contain key %s'%(path+fname, key)
    
    return header, f
    
def asc_to_ndarray(fname, path='./'):
    """
    Extracts long, lat, data from an ascii-format file.
    Data is a masked array if the header contains NODATA_value
    """
    header, f = get_header(fname, path)
    
    ncols = header['ncols']
    nrows = header['nrows']
    cellsize = header['cellsize']
    
    long = header['xllcorner'] + np.arange(ncols) * cellsize
    lat = header['yllcorner'] + np.arange(nrows) * cellsize
    data = np.loadtxt(f)
    f.close()
    
    data = data[::-1,:]
    if header.has_key('NODATA_value'):
        data = np.ma.masked_array(data, mask=data==header['NODATA_value'])
    
    return long, lat, data


def exportAscii (arr,filename,headerDict,mask=0):

    import numpy as np
    
    # create output file link
    f = file(filename,"w")
    
    # write in header
    f.write('ncols\t'+str(headerDict['ncols'])+'\n')
    f.write('nrows\t'+str(headerDict['nrows'])+'\n')
    f.write('xllcorner\t'+str(headerDict['xllcorner'])+'\n')
    f.write('yllcorner\t'+str(headerDict['yllcorner'])+'\n')
    f.write('cellsize\t'+str(headerDict['cellsize'])+'\n')
    f.write('NODATA_value\t'+str(headerDict['NODATA_value'])+'\n')
    
    # write in main array
    
    # optionally apply mask - specified by passing a mask array (0s and 1s) - 0s will be set to NODATA_value
    if type(mask)!=int:
        # perform check that the number of rows and columns is the same in both 1km grids    
        if (np.shape(mask) != np.shape(arr)):
            print 'WARNING!! mask supplied to exportAscii has wrong shape!! (mask = '+str(np.shape(mask))+' and array = '+str(np.shape(arr))+'): WILL NOT APPLY MASK!!'
        else:
            arr[mask==0]=headerDict['NODATA_value'] 

    np.savetxt(f, arr)
    f.close()
