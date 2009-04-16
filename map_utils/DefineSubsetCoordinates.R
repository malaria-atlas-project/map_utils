########################################################################
returnNewHeader<-function(bottomOBS,topOBS,leftOBS,rightOBS){

 ## work out new yllcorner and nrows
    if(is.na(bottomOBS)) NrowsBelow<-0
    if(!is.na(bottomOBS))NrowsBelow<-floor(((bottomOBS- yllcorner) / cellsize))
    yllcornerNEW<-yllcorner+(NrowsBelow*cellsize)
    if(is.na(topOBS))NrowsWithin<-nrows-NrowsBelow
    if(!is.na(topOBS))NrowsWithin<-ceiling(((topOBS - yllcornerNEW) / cellsize))

 ## work out new xllcorner and ncols
    if(is.na(leftOBS)) Ncolsleft<-0
    if(!is.na(leftOBS))Ncolsleft<-floor(((leftOBS- xllcorner) / cellsize))
    xllcornerNEW<-xllcorner+(Ncolsleft*cellsize)
    if(is.na(rightOBS))NcolsWithin<-ncols-Ncolsleft
    if(!is.na(rightOBS))NcolsWithin<-ceiling(((rightOBS - xllcornerNEW) / cellsize))

 ## work out row and col positions on input grid
    topRow<-(nrows - (NrowsBelow+NrowsWithin))+1
    bottomRow<-(topRow+NrowsWithin)-1
    leftCol<-Ncolsleft+1
    rightCol<-Ncolsleft+NcolsWithin

 ## print out header
    print(paste("ncols",NcolsWithin))
    print(paste("nrows",NrowsWithin))
    print(paste("xllcorner",xllcornerNEW))
    print(paste("yllcorner",yllcornerNEW))
    print(paste("cellsize",cellsize))
    print("NODATA_value  -9999")

 ## print out row and col positions
    print(paste(""))
    print(paste("topRow",topRow))
    print(paste("bottomRow",bottomRow))
    print(paste("leftCol",leftCol))
    print(paste("rightCol",rightCol))
}
#######################################################################

 ## define original header
    ncols<-         8664
    nrows<-         3384
    xllcorner<-     -180
    yllcorner<-     -57
    cellsize<-      0.04166665

 ## define observed edge locations (NA denotes same as original) and call function

  # AM
    bottomOBS<- -24.397
    topOBS <-21.756
    leftOBS<--95.111
    rightOBS <--38.316
    returnNewHeader(bottomOBS,topOBS,leftOBS,rightOBS)

  # AF
    bottomOBS<--30.336
    topOBS <-25.963
    leftOBS<--18.395
    rightOBS <-54.485
    returnNewHeader(bottomOBS,topOBS,leftOBS,rightOBS)

  # AS
    bottomOBS<--20.644
    topOBS <-41.595
    leftOBS<-38.336
    rightOBS <-170.936
    returnNewHeader(bottomOBS,topOBS,leftOBS,rightOBS)



   # kenya crude
    bottomOBS<--4.9
    topOBS <-4.8
    leftOBS<-33.5
    rightOBS <-42
    returnNewHeader(bottomOBS,topOBS,leftOBS,rightOBS) 


