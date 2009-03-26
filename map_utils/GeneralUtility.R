writeTableWithNames<-function(table,names,filepath,SEP=" "){

# names must be a list in python

table=data.frame(table)
names(table)=as.vector(as.character(names))
write.table(table,file=filepath,row.names=F,sep=SEP)

}