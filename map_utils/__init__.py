from checkAndBuildPaths import checkAndBuildPaths
from quantile_funs import *
from getAsciiheaderFromTemplateHDF5 import *
from exportAscii import *
#from generic_mbg import *
from exportHDF5asASCII import *
#from variograms import *


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
        to = to[2:]+to[:2]
        
    if not frm[1]==to[1]:
        g=g[::-1,:]
    if not frm[3]==to[3]:
        g=g[:,::-1]
    return g
