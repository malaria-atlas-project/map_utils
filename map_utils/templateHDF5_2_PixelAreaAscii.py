
# import libraries
import numpy as np
import tables as tb
from map_utils import getAsciiheaderFromTemplateHDF5
from geodata_utils import cylindrical_pixel_area
from map_utils import exportAscii

########################################################################################################
def makePixelAreaArray(inputHDF5template_path,outputASCII_path):

    # import header information from a template hdf5 file
    hdrDict=getAsciiheaderFromTemplateHDF5(inputHDF5template_path)

    # for first column in grid:

    ## define vector of lower edge latitudes for each pixel in a column from the grid
    llclat = hdrDict['yllcorner'] + (np.arange(hdrDict['nrows'])*hdrDict['cellsize'])

    ## define vector of upper edge latitudes
    urclat = llclat+hdrDict['cellsize']

    ## define left-hand edge longitude
    llclon = hdrDict['xllcorner']

    ## define right-hand edge longitude
    urclon = llclon+hdrDict['cellsize']

    # call funtion to return vector of areas for pixels in this column
    pixel_areas_firstcolumn = cylindrical_pixel_area(llclon, llclat, urclon, urclat)

    # now duplicate this column of pixel areas accross the full width of the array
    pixel_areas_firstcolumn = pixel_areas_firstcolumn[::-1]   
    pixel_areas_array = np.vstack(((pixel_areas_firstcolumn,)*hdrDict['ncols'])).T

    # export array as ascii
    exportAscii (pixel_areas_array,outputASCII_path,hdrDict)
########################################################################################################

makePixelAreaArray('/home/pwg/mbg-world/datafiles/auxiliary_data/GridsForCS/gr075km_y-x+.hdf5','/home/pwg/mbg-world/datafiles/auxiliary_data/GridsForCS/pixarea5km_y-x+.asc')
makePixelAreaArray('/home/pwg/mbg-world/datafiles/auxiliary_data/GridsForCS/gr071km_y-x+.hdf5','/home/pwg/mbg-world/datafiles/auxiliary_data/GridsForCS/pixarea1km_y-x+.asc')
