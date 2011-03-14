import warnings
import sys

try:
    from templateHDF5_2_PixelAreaAscii import *
    from getAsciiheaderFromTemplateHDF5 import *    
except:
    cls, inst, tb = sys.exc_info()
    print 'Failed to import a module. Error: ' + inst[0]

from quantile_funs import *
from exportAscii import *
from exportHDF5asASCII import *
from geodata_utils import *
from hdf5_utils import *
from zipped_cru import *
from merge_close_points import *
from tif2array import *

from recarray_utils import *
from clip_raster import *

#from EmpiricalCovarianceLib import *

from lazy_data_dir import *

try:
    from amazon_ec import *
    from boto_PYlib import *
except:
    print 'Failed to improt amazon_ec and boto_PYlib'

try:
    from checkAndBuildPaths import *
except:
    print 'Failed to import checkAndBuildPaths'

try:
    from modis_utils import *
except:
    print 'Failed to import modis_utils'

try:
    from variograms import *
except:
    print 'Failed to import variograms'

# try:
from shapefile_utils import *
# except:
#     print 'Failed to import shapefile_utils'

from top_raster import *