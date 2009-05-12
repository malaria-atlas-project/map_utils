def getAsciiheaderFromTemplateHDF5 (hdfFilePath):

    import tables as tb
    
    # open link to hdf5 file containing ascii-like header info
    hf = tb.openFile(hdfFilePath)   
    hdrInfo = hf.root._v_attrs
    
    ########TEMP - derive cellsize manually beacause currently missing from hdf5s from ascii
    #cellsize = (hdrInfo.maxx - hdrInfo.minx) / hdrInfo.ncols
    ############
    
    # construct dictionary of ascii header info
    hdrDict={'ncols':hdrInfo.ncols,'nrows':hdrInfo.nrows,'xllcorner':hdrInfo.minx,'yllcorner':hdrInfo.miny,'cellsize':hdrInfo.cellsize,'NODATA_value':hdrInfo.missing}   
    ######TEMP because cellsize missing from asciis currently 
    #hdrDict={'ncols':hdrInfo.ncols,'nrows':hdrInfo.nrows,'xllcorner':hdrInfo.minx,'yllcorner':hdrInfo.miny,'cellsize':cellsize,'NODATA_value':hdrInfo.missing}    
    ############

    return(hdrDict)
