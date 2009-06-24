from checkAndBuildPaths import checkAndBuildPaths
from quantile_funs import *
from getAsciiheaderFromTemplateHDF5 import *
from exportAscii import *
from exportHDF5asASCII import *
from amazon_ec import *
from boto_PYlib import *
#from EmpiricalCovarianceLib import *

try:
    from variograms import *
except:
    print 'Failed to import variograms'

try:
    from shapefile_utils import *
except:
    print 'Failed to import shapefiles'

def validate_format_str(st):
    for i in [0,2]:
        if not st[i] in ['x','y']:
            raise ValueError, 'Directions must be x or y'
    for j in [1,3]:
        if not st[j] in ['-', '+']:
            raise ValueError, 'Orders must be + or -'
            
    if st[0]==st[2]:
        raise ValueError, 'Directions must be different'
    
    
def grid_convert(g, frm, to, validate=False):
    """Converts a grid to a new layout.
      - g : 2d array
      - frm : format string
      - to : format string

      Example format strings:
        - x+y+ (the way Anand does it) means that 
            - g[i+1,j] is west of g[i,j]
            - g[i,j+1] is north of g[i,j]
        - y-x+ (map view) means that 
            - g[i+1,j] is south of g[i,j]
            - g[i,j+1] is west of g[i,j]"""

    # Validate format strings
    if validate:
        for st in [frm, to]:
            validate_format_str(st)

    # Transpose if necessary
    if not frm[0]==to[0]:
        g = g.T

    first_dir = to[1]
    if not first_dir == frm[frm.find(to[0])+1]:
        # print 'First mismatch'
        g=g[::-1,:]

    sec_dir = to[3]
    if not sec_dir == frm[frm.find(to[2])+1]:
        # print 'Second mismatch'
        g=g[:,::-1]

    # print first_dir, sec_dir
    return g