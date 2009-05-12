def exportHDF5asASCII (hdfFilePath,outputpath):

    from map_utils import getAsciiheaderFromTemplateHDF5
    from map_utils import exportAscii
    import tables as tb
    
    # open link to hdf5 file
    hf = tb.openFile(hdfFilePath, mode = "r")

    # get main array
    inputarray = hf.root.data[:]   

    # get header info as dictionary
    hdrDict = getAsciiheaderFromTemplateHDF5 (hdfFilePath)

    # export as ascii
    exportAscii(inputarray,outputpath,hdrDict)


    