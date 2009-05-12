import numpy as np
import pylab as pl
from directions import *

__all__ = ['plot_variogram']

def find(value, bin_edges):
    """
    helper function for variogram.
    """
    for k in np.xrange(len(bin_edges)):
        if value<bin_edges[k]:
            break
    return k-1

def variogram(d,x,nb,a,h,m=-1.,r=6379.1,plot=True,ti='',xl='distance, km'):
    """
    blf,bw,bl,c,n = plot_variogram(d,x,nb,a,h,m=-1.,r=6379.1,ti='',xl='distance, km')
    Creates and plots a variogram.
    
    Input:
    - d: Data or response variable
    - x: Locations associated with response variable, first column long, second lat.
    - nb: Number of bins.
    - a: Central angles (for directional variogram)
    - h: Halfwidth angle
    - m: Maximum distance to consider
    - r: Radius of the 'earth'
    - plot: Whether to generate plots
    - ti: Title of plot
    - xl: X label of plot
    
    Output:
    - blf: Left edges of bins
    - bw: Width of bins
    - bl: Centers of bins
    - c: Actual variogram
    - n: Number of pairs in each bin at each angle.
    
    See also: dvar
    """
    
    blf,bw,bl,c,n = dvar(d,x,nb,a,h,r,m)
    
    if plot:
        pl.figure(figsize=(12,6))
        pl.axis('off')
        pl.title(ti)

        pl.subplot(1,2,1)
        for i in range(len(a)):
            pl.plot(bl,c[i,:],label=int(a[i]*180/np.pi).__str__(),linestyle='-',marker='.',markersize=8)
        pl.xlabel(xl)
        pl.legend()

        pl.subplot(1,2,2)
        for i in range(len(a)):
            pl.plot(bl,n[i,:],label=int(a[i]*180/np.pi).__str__(),linestyle='-',marker='.',markersize=8)
            pl.ylabel("Number of pairs")
            pl.xlabel(xl)

    return blf,bw,bl,c,n