
from map_utils import checkAndBuildPaths
import tables as tb

def BuildAsciiParamsInHDF5(hdfFilePath,CELLTOLLERANCE = 1e-6,missingDefault=-9999,overwrite=False):

    ''' Takes and hdf5 grid file, which must have attributes: data, long, and lat
        will then work out the ascii header parameters for theis grid and add them to _v_attrs
        
        Input parameters;
        hdfFilePath (string): location including filename of hdf5 file
        CELLTOLLERANCE (float): when inferring the cellsize by calculating difference between stated cell
                                positions in lat/long, how much disparity are we happy with?
        missingDefault (float or int): what value shall we use in the ascii header for missing
        overwrite (Boolean): if the hdf5 file alrady has a given piece of header inf, shall we overwrite with ehat we infer here?
        
        returns:
        nothing returned, but potentially changes hdf5 file in-situ
    ''' 

    #check hdf5 file exists, and exxit if not
    if(checkAndBuildPaths(hdfFilePath,VERBOSE=True,BUILD=False)==-9999):
        raise ValueError ('hdf5 file does not exist')    
    
    # Initialize hdf5 file in append mode so can add new attributes
    outHDF5 = tb.openFile(hdfFilePath, mode='a')
    lon =  outHDF5.root.lon
    lat =  outHDF5.root.lat  
    
    # check in y-x+ format, or else not configured
    if outHDF5.root.data.attrs.view != 'y-x+':
        raise ValueError ('hdf5 file: '+str(hdfFilePath)+'\nis not in y-x+ view, and function not configured to handle any other')    

    # infer ascii parameters in turn, for each first checking if it it already exists, and optionally overwriting
    ncols = len(lon)
    if hasattr(outHDF5.root._v_attrs,'ncols'):
        if(outHDF5.root._v_attrs.ncols !=ncols):
            print ('existing ncols value ('+str(outHDF5.root._v_attrs.ncols)+' != that calculated here '+str(ncols))

        if overwrite==False:
            print ('hdf5 file at'+str(hdfFilePath)+',already has attribute ncols and overwrite==FALSE')
        else:
            print ('hdf5 file at'+str(hdfFilePath)+',already has attribute ncols, but replacing because overwrite==True')
            outHDF5.root._v_attrs.ncols = ncols
    else:
        outHDF5.root._v_attrs.ncols = ncols     

    nrows = len(lat)
    if hasattr(outHDF5.root._v_attrs,'nrows'):
        if(outHDF5.root._v_attrs.nrows !=nrows):
            print ('existing nrows value ('+str(outHDF5.root._v_attrs.nrows)+' != that calculated here '+str(nrows))

        if overwrite==False:
            print ('hdf5 file at'+str(hdfFilePath)+',already has attribute nrows and overwrite==FALSE')
        else:
            print ('hdf5 file at'+str(hdfFilePath)+',already has attribute nrows, but replacing because overwrite==True')
            outHDF5.root._v_attrs.nrows = nrows
    else:
        outHDF5.root._v_attrs.nrows = nrows  


    minx = min(lon)
    if hasattr(outHDF5.root._v_attrs,'minx'):
        if(outHDF5.root._v_attrs.minx !=minx):
            print ('existing minx value ('+str(outHDF5.root._v_attrs.minx)+' != that calculated here '+str(minx))

        if overwrite==False:
            print ('hdf5 file at'+str(hdfFilePath)+',already has attribute minx and overwrite==FALSE')
        else:
            print ('hdf5 file at'+str(hdfFilePath)+',already has attribute minx, but replacing because overwrite==True')
            outHDF5.root._v_attrs.minx = minx
    else:
        outHDF5.root._v_attrs.minx = minx  

    maxx = max(lon)
    if hasattr(outHDF5.root._v_attrs,'maxx'):
        if(outHDF5.root._v_attrs.maxx !=maxx):
            print ('existing maxx value ('+str(outHDF5.root._v_attrs.maxx)+' != that calculated here '+str(maxx))

        if overwrite==False:
            print ('hdf5 file at'+str(hdfFilePath)+',already has attribute maxx and overwrite==FALSE')
        else:
            print ('hdf5 file at'+str(hdfFilePath)+',already has attribute maxx, but replacing because overwrite==True')
            outHDF5.root._v_attrs.maxx = maxx
    else:
        outHDF5.root._v_attrs.maxx = maxx

    miny = min(lat)
    if hasattr(outHDF5.root._v_attrs,'miny'):
        if(outHDF5.root._v_attrs.miny !=miny):
            print ('existing maxx value ('+str(outHDF5.root._v_attrs.miny)+' != that calculated here '+str(miny))

        if overwrite==False:
            print ('hdf5 file at'+str(hdfFilePath)+',already has attribute miny and overwrite==FALSE')
        else:
            print ('hdf5 file at'+str(hdfFilePath)+',already has attribute miny, but replacing because overwrite==True')
            outHDF5.root._v_attrs.miny = miny
    else:
        outHDF5.root._v_attrs.miny = miny
        
        
    maxy = max(lat)
    if hasattr(outHDF5.root._v_attrs,'maxy'):
        if(outHDF5.root._v_attrs.maxy !=maxy):
            print ('existing maxy value ('+str(outHDF5.root._v_attrs.maxy)+' != that calculated here '+str(maxy))

        if overwrite==False:
            print ('hdf5 file at'+str(hdfFilePath)+',already has attribute maxy and overwrite==FALSE')
        else:
            print ('hdf5 file at'+str(hdfFilePath)+',already has attribute maxy, but replacing because overwrite==True')
            outHDF5.root._v_attrs.maxy = maxy
    else:
        outHDF5.root._v_attrs.maxy = maxy        
        
    cellsizeX = lon[1] - lon[0]
    cellsizeY = lat[1] - lat[0]    
    if(abs(cellsizeX - cellsizeY)>CELLTOLLERANCE):
        print ('Inferred cell sizes from lat '+str(cellsizeY)+' and long ' +str(cellsizeX)+' do not match')
        
    cellsize = cellsizeX
    if hasattr(outHDF5.root._v_attrs,'cellsize'):
        if(outHDF5.root._v_attrs.cellsize !=cellsize):
            print ('existing cellsize value ('+str(outHDF5.root._v_attrs.cellsize)+' != that calculated here '+str(cellsize))

        if overwrite==False:
            print ('hdf5 file at'+str(hdfFilePath)+',already has attribute cellsize and overwrite==FALSE')
        else:
            print ('hdf5 file at'+str(hdfFilePath)+',already has attribute cellsize, but replacing because overwrite==True')
            outHDF5.root._v_attrs.cellsize = cellsize
    else:
        outHDF5.root._v_attrs.cellsize = cellsize                
        

    order = outHDF5.root.data.attrs.view
    if hasattr(outHDF5.root._v_attrs,'order'):
        if(outHDF5.root._v_attrs.order !=order):
            print ('existing order value ('+str(outHDF5.root._v_attrs.order)+' != that calculated here '+str(order))

        if overwrite==False:
            print ('hdf5 file at'+str(hdfFilePath)+',already has attribute order and overwrite==FALSE')
        else:
            print ('hdf5 file at'+str(hdfFilePath)+',already has attribute order, but replacing because overwrite==True')
            outHDF5.root._v_attrs.order = order
    else:
        outHDF5.root._v_attrs.order = order            

    missing = missingDefault
    if hasattr(outHDF5.root._v_attrs,'missing'):
        if(outHDF5.root._v_attrs.missing !=missing):
            print ('existing missing value ('+str(outHDF5.root._v_attrs.missing)+' != that calculated here '+str(missing))

        if overwrite==False:
            print ('hdf5 file at'+str(hdfFilePath)+',already has attribute missing and overwrite==FALSE')
        else:
            print ('hdf5 file at'+str(hdfFilePath)+',already has attribute missing, but replacing because overwrite==True')
            outHDF5.root._v_attrs.missing = missing
    else:
        outHDF5.root._v_attrs.missing = missing    

    outHDF5.close()
###############################################################################################################

#BuildAsciiParamsInHDF5("/home/pwg/mbg-world/datafiles/auxiliary_data/ndvi.mean.geographic.world.2001-to-2006.hdf5",CELLTOLLERANCE = 1e-6,missingDefault=-9999,overwrite=False)

#BuildAsciiParamsInHDF5("/home/pwg/mbg-world/datafiles/auxiliary_data/ndvi.annual-amplitude.geographic.world.2001-to-2006.hdf5",CELLTOLLERANCE = 1e-6,missingDefault=-9999,overwrite=False)

#BuildAsciiParamsInHDF5("/home/pwg/mbg-world/datafiles/auxiliary_data/evi.mean.geographic.world.2001-to-2005.hdf5",CELLTOLLERANCE = 1e-6,missingDefault=-9999,overwrite=False)

#BuildAsciiParamsInHDF5("/home/pwg/mbg-world/datafiles/auxiliary_data/evi.minimum.geographic.world.2001-to-2006.hdf5",CELLTOLLERANCE = 1e-6,missingDefault=-9999,overwrite=False)

#BuildAsciiParamsInHDF5("/home/pwg/mbg-world/datafiles/auxiliary_data/raw-data.elevation.geographic.world.version-5.hdf5",CELLTOLLERANCE = 1e-6,missingDefault=-9999,overwrite=False)
    
    
