import ImageFile
import numpy as np

__all__ = ['tif2array']

def tif2array(fname):
    """Convert image to Numeric array"""
    im = ImageFile.Image.open(fname)
    print im.size
    print im.mode
    if im.mode not in ("L", "I;16", "F"):
        raise ValueError, "can only convert single-layer images"
    if im.mode == "L":
        a = np.fromstring(im.tostring(), np.dtype('uint8'))
    if im.mode == "I;16":
        a = np.fromstring(im.tostring(), np.dtype('int16'))
    if im.mode == "F":
        a = np.fromstring(im.tostring(), np.dtype('float32'))
    return a.reshape(im.size[1], im.size[0])
     
if __name__=='__main__':
    a = tif2array('GLOBCOVER_200412_200606_V2.2_Global_CLA.tif')
