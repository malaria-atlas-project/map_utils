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
