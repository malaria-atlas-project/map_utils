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
    bottomOBS<- -19.417175
    topOBS <-20.458679
    leftOBS<--91.466797
    rightOBS <--42.668518
    returnNewHeader(bottomOBS,topOBS,leftOBS,rightOBS)

  # AF
    bottomOBS<--29.568787
    topOBS <-25.176086
    leftOBS<--18.118103
    rightOBS <-53.439697
    returnNewHeader(bottomOBS,topOBS,leftOBS,rightOBS)

  # AS
    bottomOBS<--20.644
    topOBS <-41.595
    leftOBS<-38.336
    rightOBS <-170.936
    returnNewHeader(bottomOBS,topOBS,leftOBS,rightOBS)



   # kenya 
    bottomOBS<--4.8103
    topOBS <-4.832
    leftOBS<-33.9240
    rightOBS <-41.837
    returnNewHeader(bottomOBS,topOBS,leftOBS,rightOBS) 
    
  
    # Test square in S malawi - includes a high and low focus and an urban area
    bottomOBS<--16.47821
    topOBS <--15.424316
    leftOBS<-34.451721
    rightOBS <-35.16449
    returnNewHeader(bottomOBS,topOBS,leftOBS,rightOBS)    
   
    bottomOBS<--17.0687
    topOBS <--14.8723
    leftOBS<-33.29528
    rightOBS <-36.50061
    returnNewHeader(bottomOBS,topOBS,leftOBS,rightOBS)       
   
   
    #AS1
    bottomOBS<-4.428101
    topOBS <-37.83313
    leftOBS<-52.282104
    rightOBS <-126.893677
    returnNewHeader(bottomOBS,topOBS,leftOBS,rightOBS)    

    #AS2
    bottomOBS<--21.044678
    topOBS <-7.43573
    leftOBS<-94.640686
    rightOBS <-170.763672
    returnNewHeader(bottomOBS,topOBS,leftOBS,rightOBS)    

   #AM small test square
   bottomOBS<--12.836975
   topOBS <--11.783081
   leftOBS<--64.039612
   rightOBS <--63.326904
   returnNewHeader(bottomOBS,topOBS,leftOBS,rightOBS)      


