import pymc as pm
import tables as tb
import numpy as np
from exportAscii import asc_to_ndarray

def add_time(x,t):
    return vstack((x.T, t*np.ones(x.shape[0]))).T

def asc_to_locs(fname):
    lon,lat,data = asc_to_ndarray(fname)
    lon,lat = [dir[True-data.mask] for dir in np.meshgrid(lon,lat)]
    return np.vstack((lon,lat)).T
    

def hdf5_to_samps(chain, x, burn, n_total):

if __name__ == '__main__':
    from pylab import *
    import matplotlib
    x= asc_to_locs('frame3_10k.asc.txt')    
    matplotlib.interactive('False')
    plot(x[:,0],x[:,1],'k.',markersize=1)
    show()
    
    