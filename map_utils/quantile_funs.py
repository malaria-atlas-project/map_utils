#############################################################################################################################################
def quantile(inarray, probs):

    # inarray must be 1-d numpy array 
    # probs must be same and contain desired prob quantiles between 0 and 1

    from numpy import sort, maximum

    sorted_inarray = sort(inarray)
    outarray = sorted_inarray[maximum((probs*inarray.size-1).astype("int32"),0)]

    return outarray

#############################################################################################################################################
def row_quantile(inarray, probs):

    from numpy import reshape,repeat,shape

    arrayshape=inarray.shape
    if len(arrayshape)!=2: print "ERROR!!! function row_quantile is only for 2-d arrays -this has "+str(len(arrayshape))+"\n"
    nrow = arrayshape[0]
    outarray = repeat(-9999.,nrow*len(probs)).reshape(nrow,len(probs))
    for i in xrange(0,nrow):
        outarray[i,:] = quantile(inarray[i,:], probs)

    return outarray

#############################################################################################################################################
def col_quantile(inarray, probs):

    from numpy import reshape,repeat,shape

    arrayshape=inarray.shape
    if len(arrayshape)!=2: print "ERROR!!! function row_quantile is only for 2-d arrays -this has "+str(len(arrayshape))+"\n"
    ncol = arrayshape[1]
    outarray = repeat(-9999.,ncol*len(probs)).reshape(ncol,len(probs))
    for i in xrange(0,ncol):
        outarray[:,i] = quantile(inarray[:,i], probs)

    return(outarray)

#############################################################################################################################################
