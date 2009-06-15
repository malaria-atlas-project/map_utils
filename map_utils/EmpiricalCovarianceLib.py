import numpy as np
import tables as tb
from rpy import *
from math import sqrt

def getEmpiricalCovarianceFunction(xy,z,mu,nbins=None, cutoff = 0.8):

#    from IPython.Debugger import Pdb
#    Pdb(color_scheme='Linux').set_trace()

    # work out if we passed a two- or one-column set of locations
    if (len(np.shape(xy))==1):
        d1=xy
        d2=None
        
    if (len(np.shape(xy))==2):
        d1=xy[:,0]
        d2=xy[:,1]
        

    # get distance matrix

    ## if no second dimension supplied, assume we are evaluating along a transect, or through time:
    if (d2 is None):
        X = np.vstack(((d1,))*len(d1))
        DX = X-X.T
        Dxy = np.sqrt(DX*DX)
        
    ## if two dimensions supplied, assume we want cross-distances (i.e. we have two spatial dimensions)
    if (d2 is not None):
        X = np.vstack(((d1,))*len(d1))
        dX = X-X.T
        Y = np.vstack(((d2,))*len(d2))
        dY = Y-Y.T
        Dxy = np.sqrt(dX*dX +dY*dY)

    # get empirical point-to-point covariance matrix
    temp = z-mu
    TEMP = np.vstack(((temp,))*len(temp))
    TEMP = TEMP*TEMP.T
    
    # convert lag and C matrices to vector based only on lower triangle(and diagonal)
    IDmat = np.ones(np.product(np.shape(TEMP))).reshape(np.shape(TEMP))
    Cvector = TEMP[np.where(np.tril(IDmat,k=0)==1)]
    Dvector = Dxy[np.where(np.tril(IDmat,k=0)==1)]

    # if we are not binning, then return vectors of all pairwise covariances and lags
    if (nbins is None): return ({'C':Cvector,'lag':Dvector})
    
    # if we are binning
    
    ## establish maximum distance, and get nbins equal bins along this distance
    mxlag = Dvector.max()*cutoff
    binWidth = mxlag/(nbins)
    binMins = np.arange(nbins)*binWidth
    binMaxs = binMins+binWidth
    
    # loop through bins and get expected covariance
    Cbins = np.ones(nbins)*-9999
    Dbins = np.ones(nbins)*-9999
    for i in np.arange(nbins):
        lagID = np.where((Dvector>=binMins[i]) & (Dvector<binMaxs[i]))
        if (len(lagID[0])>0):  # i.e only populate this lag if there is any data in it
            Cbins[i]=np.mean(Cvector[lagID])
            Dbins[i]=np.mean(Dvector[lagID])
        
    # remove bins with no data
    IDkeep = np.where((Cbins!=-9999) & (Dbins!=-9999))
    Cbins = Cbins[IDkeep]
    Dbins = Dbins[IDkeep]
    
    return ({'C':Cbins,'lag':Dbins})

def getEmpiricalCovarianceFunction_STmarginals(xyt,z,mu,margTol_S,margTol_T,nbins=None, cutoff = 0.8):

#    from IPython.Debugger import Pdb
#    Pdb(color_scheme='Linux').set_trace()

    # assign vectors
    d1=xyt[:,0]
    d2=xyt[:,1]
    t=xyt[:,2]

    ## get temporal distance matrix
    Tmat = np.vstack(((t,))*len(t))
    Dt = Tmat-Tmat.T
    Dt = np.sqrt(Dt*Dt)
        
    # get spatial distance matrix
    X = np.vstack(((d1,))*len(d1))
    dX = X-X.T
    Y = np.vstack(((d2,))*len(d2))
    dY = Y-Y.T
    Dxy = np.sqrt(dX*dX +dY*dY)

    # get empirical point-to-point covariance matrix
    temp = z-mu
    TEMP = np.vstack(((temp,))*len(temp))
    TEMP = TEMP*TEMP.T
    
    # convert lag and C matrices to vector based only on lower triangle(and diagonal)
    IDmat = np.ones(np.product(np.shape(TEMP))).reshape(np.shape(TEMP))
    Cvector = TEMP[np.where(np.tril(IDmat,k=0)==1)]
    Dvector_s = Dxy[np.where(np.tril(IDmat,k=0)==1)]
    Dvector_t = Dt[np.where(np.tril(IDmat,k=0)==1)]

    # if we are not binning, then return a dictionary for both space and time containng vectors of all pairwise covariances and lags
    if (nbins is None):
        retDict = {'space':{'C':Cvector,'lag':Dvector_s},'time':{'C':Cvector,'lag':Dvector_t}}
        return (retDict)
    
    # if we are binning

    # extract from lag and covariance vectors only those pairs within specified threshold in orthogonal axis (i.e leave only time- and space-marginalish pairs)
    marginalID_s = np.where(Dvector_t<=margTol_T)
    marginalID_t = np.where(Dvector_s<=margTol_S)

    Cvector_s = Cvector[marginalID_s]
    Cvector_t = Cvector[marginalID_t]
    Dvector_s = Dvector_s[marginalID_s]
    Dvector_t = Dvector_t[marginalID_t]

    # now bin for space:
    
    ## establish maximum distance, and get nbins equal bins along this distance
    mxlag = Dvector_s.max()*cutoff
    binWidth = mxlag/(nbins)
    binMins = np.arange(nbins)*binWidth
    binMaxs = binMins+binWidth
    
    # loop through bins and get expected covariance
    Cbins_s = np.ones(nbins)*-9999
    Dbins_s = np.ones(nbins)*-9999
    for i in np.arange(nbins):
        lagID = np.where((Dvector_s>=binMins[i]) & (Dvector_s<binMaxs[i]))
        if (len(lagID[0])>0):  # i.e only populate this lag if there is any data in it
            Cbins_s[i]=np.mean(Cvector_s[lagID])
            Dbins_s[i]=np.mean(Dvector_s[lagID])
        
    # remove bins with no data
    IDkeep = np.where((Cbins_s!=-9999) & (Dbins_s!=-9999))
    Cbins_s = Cbins_s[IDkeep]
    Dbins_s = Dbins_s[IDkeep]
    
    # now bin for time:
    
    ## establish maximum distance, and get nbins equal bins along this distance
    mxlag = Dvector_t.max()*cutoff
    binWidth = mxlag/(nbins)
    binMins = np.arange(nbins)*binWidth
    binMaxs = binMins+binWidth
    
    # loop through bins and get expected covariance
    Cbins_t = np.ones(nbins)*-9999
    Dbins_t = np.ones(nbins)*-9999
    for i in np.arange(nbins):
        lagID = np.where((Dvector_t>=binMins[i]) & (Dvector_t<binMaxs[i]))
        if (len(lagID[0])>0):  # i.e only populate this lag if there is any data in it
            Cbins_t[i]=np.mean(Cvector_t[lagID])
            Dbins_t[i]=np.mean(Dvector_t[lagID])
        
    # remove bins with no data
    IDkeep = np.where((Cbins_t!=-9999) & (Dbins_t!=-9999))
    Cbins_t = Cbins_t[IDkeep]
    Dbins_t = Dbins_t[IDkeep]

    # construct return dictionary
    retDict = {'space':{'C':Cbins_s,'lag':Dbins_s},'time':{'C':Cbins_t,'lag':Dbins_t}}
    return (retDict)

def plotEmpiricalCovarianceFunction(EmpCovFuncDict,CovModelObj=None,spaceORtime="space", cutoff = 0.8, title=None):

    # get starting axis limits from empirical covariacne function
    if (cutoff is None): XLIM=(0,EmpCovFuncDict['lag'].max())
    if (cutoff is not None): XLIM=(0,EmpCovFuncDict['lag'].max()*cutoff)
    ymin = np.min((EmpCovFuncDict['C'].min(),0))    
    ymax = EmpCovFuncDict['C'].max()
        
    # if passed, get theoretical covariance model:
    if (CovModelObj is not None):

        xplot = np.arange(100)*(XLIM[1]/100)

        # if spatial, add both X and Y orientations:
        if (spaceORtime=="space"):

            yplotYCOV = CovModelObj([[0,0,0]], np.vstack((np.zeros(len(xplot)),xplot,np.zeros(len(xplot)))).T)
            yplotYCOV = np.asarray(yplotYCOV).squeeze()
            if (np.max(yplotYCOV)>ymax): ymax = np.max(yplotYCOV)     
            if (np.min(yplotYCOV)<ymin): ymin = np.min(yplotYCOV)
            
            yplotXCOV = CovModelObj([[0,0,0]], np.vstack((xplot,np.zeros(len(xplot)),np.zeros(len(xplot)))).T)
            yplotXCOV = np.asarray(yplotXCOV).squeeze()
            if (np.max(yplotXCOV)>ymax): ymax = np.max(yplotXCOV)     
            if (np.min(yplotXCOV)<ymin): ymin = np.min(yplotXCOV)

        if (spaceORtime=="time"):

            yplotTCOV = CovModelObj([[0,0,0]], np.vstack((np.zeros(len(xplot)),np.zeros(len(xplot)),xplot)).T)
            yplotTCOV = np.asarray(yplotTCOV).squeeze()
            if (np.max(yplotTCOV)>ymax): ymax = np.max(yplotTCOV)     
            if (np.min(yplotTCOV)<ymin): ymin = np.min(yplotTCOV)

    # make up base plot of empirical covairance
    YLIM = (ymin,ymax)
    if (spaceORtime=="space"): XLAB = "lag (s)"
    if (spaceORtime=="time"): XLAB = "lag (t)"
    r.plot(EmpCovFuncDict['lag'],EmpCovFuncDict['C'],ylim=YLIM,xlim=XLIM,xlab=XLAB,ylab="covariance")

    # optionally add theoretical covaraicne functions 
    if (CovModelObj is not None):
        if (spaceORtime=="space"):
            r.lines(xplot,yplotXCOV,col=3)
            r.lines(xplot,yplotYCOV,col=4)
        if (spaceORtime=="time"):
            r.lines(xplot,yplotTCOV,col=2)
    
    # if passed, add plot title
    if (title is not None):
        r.title(main=title)

