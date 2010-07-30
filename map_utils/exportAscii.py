import numpy as np
import string
from geodata_utils import grid_convert
import os


__all__ = ['asc_to_ndarray','exportAscii', 'get_header', 'reexport_ascii','exportAscii2', 'flt_to_ndarray', 'export_flt'] + ['sys_endian_code', 'npfile']

import sys


sys_endian_code = (sys.byteorder == 'little') and '<' or '>'

# npfile: Authors: Matthew Brett, Travis Oliphant
# From version 0.7.1 of SciPy, subsequently removed
# SciPy license applies to class npfile:
# Copyright (c) 2001, 2002 Enthought, Inc.
# All rights reserved.
# 
# Copyright (c) 2003-2009 SciPy Developers.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#   a. Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#   b. Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#   c. Neither the name of the Enthought nor the names of its contributors
#      may be used to endorse or promote products derived from this software
#      without specific prior written permission.
# 
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.


"""
Class for reading and writing numpy arrays from / to binary files
"""

class npfile(object):
    
    ''' Class for reading and writing numpy arrays to/from files

    Inputs:
      file_name -- The complete path name to the file to open
                   or an open file-like object
      permission -- Open the file with given permissions: ('r', 'w', 'a')
                    for reading, writing, or appending.  This is the same
                    as the mode argument in the builtin open command.
      format -- The byte-ordering of the file:
                (['native', 'n'], ['ieee-le', 'l'], ['ieee-be', 'B']) for
                native, little-endian, or big-endian respectively.

    Attributes:
      endian   -- default endian code for reading / writing
      order    -- default order for reading writing ('C' or 'F')
      file     -- file object containing read / written data

    Methods:
      seek, tell, close  -- as for file objects
      rewind             -- set read position to beginning of file
      read_raw           -- read string data from file (read method of file)
      write_raw          -- write string data to file (write method of file)
      read_array         -- read numpy array from binary file data
      write_array        -- write numpy array contents to binary file

    Example use:
    >>> from StringIO import StringIO
    >>> import numpy as np
    >>> from scipy.io import npfile
    >>> arr = np.arange(10).reshape(5,2)
    >>> # Make file-like object (could also be file name)
    >>> my_file = StringIO()
    >>> npf = npfile(my_file)
    >>> npf.write_array(arr)
    >>> npf.rewind()
    >>> npf.read_array((5,2), arr.dtype)
    >>> npf.close()
    >>> # Or read write in Fortran order, Big endian
    >>> # and read back in C, system endian
    >>> my_file = StringIO()
    >>> npf = npfile(my_file, order='F', endian='>')
    >>> npf.write_array(arr)
    >>> npf.rewind()
    >>> npf.read_array((5,2), arr.dtype)
    '''

    def __init__(self, file_name,
                 permission='rb',
                 endian = 'dtype',
                 order = 'C'):
        if 'b' not in permission: permission += 'b'
        if isinstance(file_name, basestring):
            self.file = file(file_name, permission)
        else:
            try:
                closed = file_name.closed
            except AttributeError:
                raise TypeError, 'Need filename or file object as input'
            if closed:
                raise TypeError, 'File object should be open'
            self.file = file_name
        self.endian = endian
        self.order = order

    def get_endian(self):
        return self._endian
    def set_endian(self, endian_code):
        self._endian = self.parse_endian(endian_code)
    endian = property(get_endian, set_endian, None, 'get/set endian code')

    def parse_endian(self, endian_code):
        ''' Returns valid endian code from wider input options'''
        if endian_code in ['native', 'n', 'N','default', '=']:
            return sys_endian_code
        elif endian_code in ['swapped', 's', 'S']:
            return sys_endian_code == '<' and '>' or '<'
        elif endian_code in ['ieee-le','l','L','little-endian',
                             'little','le','<']:
            return '<'
        elif endian_code in ['ieee-be','B','b','big-endian',
                             'big','be', '>']:
            return '>'
        elif endian_code == 'dtype':
            return 'dtype'
        else:
            raise ValueError, "Unrecognized endian code: " + endian_code
        return

    def __del__(self):
        try:
            self.file.close()
        except:
            pass

    def close(self):
        self.file.close()

    def seek(self, *args):
        self.file.seek(*args)

    def tell(self):
        return self.file.tell()

    def rewind(self,howmany=None):
        """Rewind a file to its beginning or by a specified amount.
        """
        if howmany is None:
            self.seek(0)
        else:
            self.seek(-howmany,1)

    def read_raw(self, size=-1):
        """Read raw bytes from file as string."""
        return self.file.read(size)

    def write_raw(self, str):
        """Write string to file as raw bytes."""
        return self.file.write(str)

    def remaining_bytes(self):
        cur_pos = self.tell()
        self.seek(0, 2)
        end_pos = self.tell()
        self.seek(cur_pos)
        return end_pos - cur_pos

    def _endian_order(self, endian, order):
        ''' Housekeeping function to return endian, order from input args '''
        if endian is None:
            endian = self.endian
        else:
            endian = self.parse_endian(endian)
        if order is None:
            order = self.order
        return endian, order

    def _endian_from_dtype(self, dt):
        dt_endian = dt.byteorder
        if dt_endian == '=':
            dt_endian = sys_endian_code
        return dt_endian

    def write_array(self, data, endian=None, order=None):
        ''' Write to open file object the flattened numpy array data

        Inputs
        data      - numpy array or object convertable to array
        endian    - endianness of written data
                    (can be None, 'dtype', '<', '>')
                    (if None, get from self.endian)
        order     - order of array to write (C, F)
                    (if None from self.order)
        '''
        endian, order = self._endian_order(endian, order)
        data = np.asarray(data)
        dt_endian = self._endian_from_dtype(data.dtype)
        if not endian == 'dtype':
            if dt_endian != endian:
                data = data.byteswap()
        self.file.write(data.tostring(order=order))

    def read_array(self, dt, shape=-1, endian=None, order=None):
        '''Read data from file and return it in a numpy array.

        Inputs
        ------
        dt        - dtype of array to be read
        shape     - shape of output array, or number of elements
                    (-1 as number of elements or element in shape
                    means unknown dimension as in reshape; size
                    of array calculated from remaining bytes in file)
        endian    - endianness of data in file
                    (can be None, 'dtype', '<', '>')
                    (if None, get from self.endian)
        order     - order of array in file (C, F)
                    (if None get from self.order)

        Outputs
        arr       - array from file with given dtype (dt)
        '''
        endian, order = self._endian_order(endian, order)
        dt = np.dtype(dt)
        try:
            shape = list(shape)
        except TypeError:
            shape = [shape]
        minus_ones = shape.count(-1)
        if minus_ones == 0:
            pass
        elif minus_ones == 1:
            known_dimensions_size = -np.product(shape,axis=0) * dt.itemsize
            unknown_dimension_size, illegal = divmod(self.remaining_bytes(),
                                                     known_dimensions_size)
            if illegal:
                raise ValueError("unknown dimension doesn't match filesize")
            shape[shape.index(-1)] = unknown_dimension_size
        else:
            raise ValueError(
                "illegal -1 count; can only specify one unknown dimension")
        sz = dt.itemsize * np.product(shape)
        dt_endian = self._endian_from_dtype(dt)
        buf = self.file.read(sz)
        arr = np.ndarray(shape=shape,
                         dtype=dt,
                         buffer=buf,
                         order=order)
        if (not endian == 'dtype') and (dt_endian != endian):
            return arr.byteswap()
        return arr.copy()


def maybe_num(str):
    try:
        out = int(str)
    except:
        try:
            out = float(str)
        except:
            out = str
    return out

def get_header(fname, path='./'):
    """"
    Parses an ascii file's header to a dictionary.
    Returns it along with the rest of the file.
    """
    f = file(os.path.join(path,fname),'r')
    
    header = {}
    headlines = 0
    
    while True:
        line = f.readline()
        if len(line)==0:
            break
        clean_line = string.strip(line).split()
        key = string.strip(clean_line[0])
        val = string.strip(clean_line[-1])
        if not key[0].isalpha():
            break
        val = maybe_num(val)
        if key != 'NODATA_value':
            key = key.lower()
        header[key] = val
        headlines += 1
    
    f.close()

    # for key in ['ncols','nrows','cellsize','xllcorner','yllcorner']:
    #     if not header.has_key(key):
    #         raise KeyError, 'File %s header does not contain key %s'%(path+fname, key)
    
    return header, headlines
    

def asc_to_ndarray(fname, path='./'):
    """
    Extracts long, lat, data from an ascii-format file.
    Data is a masked array if the header contains NODATA_value
    """
    header, headlines = get_header(fname, path)
    f = file(os.path.join(path,fname),'r')
    
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

def flt_to_ndarray(fname, path='./', chunk=1e9/2):
    "fname should have no extension; the '.hdr' and '.flt' extensions will be added automatically."

    header, headlines = get_header(fname+'.hdr', path)
    from scipy import io

    ncols = header['ncols']
    nrows = header['nrows']
    cellsize = header['cellsize']
    
    long = header['xllcorner'] + np.arange(ncols) * cellsize
    lat = header['yllcorner'] + np.arange(nrows) * cellsize
    
    if header['byteorder']=='LSBFIRST':
        endian='<'
    else:
        endian='>'

    # This has to be zeros. If it's empty, there will be a memory leak while it gets filled.
    data = np.zeros((nrows,ncols), dtype='float32')
    rowchunk = max(int(chunk/4/ncols),1)
#    print 'Starting'
    import gc
    for i in xrange(0,nrows,rowchunk):
#        print i
        dfile = npfile(os.path.join(path, fname)+'.flt', order='C', endian=endian)
        dfile.seek(4*ncols*i)
        data[i:i+rowchunk,:] = dfile.read_array(np.float32, shape=data[i:i+rowchunk,:].shape)
        dfile.close()
        del dfile
        gc.collect()
    # print 'Done'
    
    # dfile = io.npfile(os.path.join(path,fname)+'.flt', order='C', endian=endian)
    # data = dfile.read_array(np.float32, shape=(nrows,ncols))
    # dfile.close()
    
    if header.has_key('NODATA_value'):
        data = np.ma.masked_array(data, mask=data==header['NODATA_value'])

    return long, lat, data
    
def export_flt(lon,lat,data,filename,view='y-x+'):
    "filename should have no extension; the '.hdr' and '.flt' extensions will be added automatically." 

    data = grid_convert(data, view, 'y-x+')
    if data.shape != (len(lat),len(lon)):
        raise ValueError, 'Data is wrong shape'
    data.fill_value=np.asscalar(np.array(-9999).astype(data.dtype))
    header = {'ncols': len(lon),
                'nrows': len(lat),
                'cellsize': lon[1]-lon[0],
                'xllcorner': lon.min(),
                'yllcorner': lat.min(),
                'NODATA_value': data.fill_value,
                'byteorder': 'LSBFIRST'}
    hfile = file(filename+'.hdr', 'w')            
    for k,v in header.iteritems():
        hfile.write('%s\t%s\r\n'%(k,v))
    hfile.close()
    dfile = npfile(filename+'.flt', order='C', endian='<', permission='w')
    dfile.write_array(data.filled().astype('float32'))
    dfile.close()

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

def exportAscii2(lon,lat,data,filename,view='y-x+'):
    "Exports longitude and latitude vectors and a data masked array to ascii."
    
    data = grid_convert(data, view, 'y-x+')
    
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
