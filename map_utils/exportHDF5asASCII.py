def exportHDF5asASCII (hdfFilePath,outputpath):

    from map_utils import getAsciiheaderFromTemplateHDF5
    from map_utils import exportAscii
    import tables as tb
    
    # open link to hdf5 file
    hf = tb.openFile(hdfFilePath, mode = "r")

    # get main array
    inputarray = hf.root.data[:]   

    # get header info as dictionary
    hdrDict = getAsciiheaderFromTemplateHDF5.getAsciiheaderFromTemplateHDF5 (hdfFilePath)

    # export as ascii
    exportAscii(inputarray,outputpath,hdrDict)

#exportHDF5asASCII ("/home/pwg/mbg-world/datafiles/auxiliary_data/GridsForCS/urb5km-e_y-x+_NBIA.hdf5","/home/pwg/mbg-world/datafiles/auxiliary_data/GridsForCS/urb5km-e_y-x+_NBIA.asc")
#exportHDF5asASCII ("/home/pwg/mbg-world/datafiles/auxiliary_data/GridsForCS/urb5km-e_y-x+_AFGH.hdf5","/home/pwg/mbg-world/datafiles/auxiliary_data/GridsForCS/urb5km-e_y-x+_AFGH.asc")
#exportHDF5asASCII ("/home/pwg/mbg-world/datafiles/auxiliary_data/GridsForCS/land5km_e2_y-x+_NBIA.hdf5","/home/pwg/mbg-world/datafiles/auxiliary_data/GridsForCS/land5km_e2_y-x+_NBIA.asc")
#exportHDF5asASCII ("/home/pwg/mbg-world/datafiles/auxiliary_data/GridsForCS/land5km_e2_y-x+_AFGH.hdf5","/home/pwg/mbg-world/datafiles/auxiliary_data/GridsForCS/land5km_e2_y-x+_AFGH.asc")

