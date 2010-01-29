import numpy as np
from map_utils import exportAscii

def coarsenAsciiGridRes(fpathin, fpathout, coarsenBy, aggregationType,overlapOption,NAoption):
    """
    creates a new ascii with resolution coarsenBy coarser than input

    coarsenBy (int): factor to coarsen by - e.g. 5 would convert a 1km grid to a 5km grid
    aggregationType (str); can be 'MEAN' or 'SUM'
    overlapOption (str): can be 'EXPAND' or 'SHRINK' - what to do if the new resolution grid dimensions do not divide an integer number of times into the old.. 
    NAoption (str): can be 'IGNORE' which allows target cells to be non NA if valid small cells are present, or 'PRESERVE' which does the oposit - any target containng an NA will be NA
    """

    # check input parameters are valid
    if ((aggregationType!='MEAN') & (aggregationType!='SUM' )):
        raise ValueError ('invalid parameter value for aggregationType: '+str(aggregationType))

    if ((overlapOption!='EXPAND') & (overlapOption!='SHRINK' ) & (overlapOption!='PROHIBITED') ):
        raise ValueError ('invalid parameter value for overlapOption: '+str(overlapOption))
    if ((overlapOption=='EXPAND') | (overlapOption=='SHRINK' ) ):
        raise ValueError ('SORRY!! have bnot yet implenmented option to expand or shrink overlap - rows and cols must divide perfectly')
    if ((NAoption!='IGNORE') & (NAoption!='PRESERVE' )):
        raise ValueError ('invalid parameter value for NAoption: '+str(NAoption))

    coarsenBy = float(coarsenBy) 

    f = file(fpathin,'r')
    
    # Extract metadata from asc file.
    ncolsIN = int(f.readline()[14:])
    nrowsIN = int(f.readline()[14:])
    xllcorner = float(f.readline()[14:])
    yllcorner = float(f.readline()[14:])
    cellsizeIN = float(f.readline()[14:])
    NODATA_value = int(f.readline()[14:])

    print 'cellsizeIN: '+str(cellsizeIN)

    # define output grid parameters (taking into account whether we are expanding or shrninking in the case of overalap)
    if overlapOption == 'PROHIBITED':
        if ((int(ncolsIN/coarsenBy)!=(ncolsIN/coarsenBy)) | (int(nrowsIN/coarsenBy)!=(nrowsIN/coarsenBy))):
            raise ValueError ('rows or cols do not divide perfectly into new resolution, and overlapOption == PROHIBIT')
        ncolsOUT = int(ncolsIN/coarsenBy)
        nrowsOUT = int(nrowsIN/coarsenBy)
    if overlapOption == 'EXPAND':
        ncolsOUT = int(np.ceil(ncolsIN/coarsenBy))
        nrowsOUT = int(np.ceil(nrowsIN/coarsenBy))
    if overlapOption == 'SHRINK':
        ncolsOUT = int(np.floor(ncolsIN/coarsenBy))
        nrowsOUT = int(np.floor(nrowsIN/coarsenBy))
    cellsizeOUT = cellsizeIN*coarsenBy

    # define output header dictionary
    headerDict = {'ncols':ncolsOUT,'nrows':nrowsOUT,'xllcorner':xllcorner,'yllcorner':yllcorner,'cellsize':cellsizeOUT,'NODATA_value':NODATA_value}

    # initialise interim grid shrunk in rows, and corresponding 1-d vector to record number of small rows aggregated in each big row (for later use in mean)
    interimGrid = np.zeros(nrowsOUT*ncolsIN).reshape(nrowsOUT,ncolsIN)
    rowDenominator=np.zeros(ncolsIN)

    # initialise final grid shrunk in both rows and columns
    outgrid = np.zeros(nrowsOUT*ncolsOUT).reshape(nrowsOUT,ncolsOUT)
    colDenominator=np.zeros(nrowsOUT)

    # loop through rows and aggregate as we go    
    aggCounter = 0
    rowIndexOUT = 0
    for i in xrange(nrowsIN):
        temp = np.fromstring(f.readline(), dtype=float, sep=' ')
        #print '\n'
        #print temp
        if len(temp)!=ncolsIN:
            raise ValueError ('input row '+str(i)+'(from top) has '+str(len(temp))+' elements, but expected '+str(ncolsIN))
        keepIndex = np.where(temp!=NODATA_value)
        interimGrid[rowIndexOUT,keepIndex]+=temp[keepIndex]
        rowDenominator[keepIndex]+=1
        aggCounter +=1

        
        if ((aggCounter==coarsenBy)):

            #print '|-------------'
            #print interimGrid[rowIndexOUT,:]  
            #print '--'
            #print rowDenominator
            #print '--'
            if aggregationType=='MEAN':
                if np.any(rowDenominator!=0): interimGrid[rowIndexOUT,np.where(rowDenominator!=0)]/=rowDenominator[np.where(rowDenominator!=0)]
            if NAoption=='IGNORE': interimGrid[rowIndexOUT,np.where(rowDenominator==0)]=NODATA_value
            if NAoption=='PRESERVE': interimGrid[rowIndexOUT,np.where(rowDenominator<coarsenBy)]=NODATA_value
            #print interimGrid[rowIndexOUT,:] 
            #print '-------------|'
            rowIndexOUT+=1 
            aggCounter=0
            rowDenominator=np.zeros(ncolsIN)

    #import pylab as pl
    #pl.imshow(interimGrid,interpolation='nearest',origin='upper')
    #pl.show()
    #from IPython.Debugger import Pdb
    #Pdb(color_scheme='Linux').set_trace()   

   
    # now loop accross columns of this interim grid and aggregate as we go            
    aggCounter = 0
    colIndexIN = 0
    colIndexOUT = 0
    for i in xrange(ncolsIN):#ncolsIN
        temp=interimGrid[:,colIndexIN]
        keepIndex = np.where(temp!=NODATA_value)
        outgrid[keepIndex,colIndexOUT] += temp[keepIndex]
        colDenominator[keepIndex]+=1
        aggCounter +=1
        colIndexIN+=1
        if ((aggCounter==coarsenBy)):
            if aggregationType=='MEAN':
                if np.any(colDenominator!=0): outgrid[np.where(colDenominator!=0),colIndexOUT]/=colDenominator[np.where(colDenominator!=0)]
            if NAoption=='IGNORE': outgrid[np.where(colDenominator==0),colIndexOUT]=NODATA_value
            if NAoption=='PRESERVE': outgrid[np.where(colDenominator<coarsenBy),colIndexOUT]=NODATA_value
            colIndexOUT+=1 
            aggCounter=0
            colDenominator=np.zeros(nrowsOUT)

    #print interimGrid[:,0:4:1]
    #print outgrid

    #from IPython.Debugger import Pdb
    #Pdb(color_scheme='Linux').set_trace()   
        
    # export shrunken ascii 
    exportAscii(outgrid,fpathout,headerDict)
    
#################
coarsenAsciiGridRes("/home/pwg/mbg-world/datafiles/auxiliary_data/GridsForCS/gr071km_y-x+.asc", "/home/pwg/mbg-world/datafiles/auxiliary_data/GridsForCS/gr075km_y-x+.asc", 5, aggregationType="SUM",overlapOption="PROHIBITED",NAoption='IGNORE')

#coarsenAsciiGridRes("/home/pwg/mbg-world/test.asc", "/home/pwg/mbg-world/datafiles/auxiliary_data/GridsForCS/testout.asc", 5, aggregationType="MEAN",overlapOption="PROHIBITED",NAoption='PRESERVE')



