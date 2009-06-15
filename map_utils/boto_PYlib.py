# Author: Pete Gething
# Date: 5 March 2009
# License: Creative Commons BY-NC-SA
####################################

# set location of file containng keys to S3
#keyPath = '/root/s3code.txt'
#import extract_params

# import libraries
import boto
from boto.s3.connection import S3Connection
import random
import sys
import string
import os
import time
import md5
import warnings
from socket import gethostname
import numpy as np
from map_utils import checkAndBuildPaths

class S3(object):
    
    def __init__(self, keyPath=None):
        if keyPath is None:
            keyPath = extract_params.keyPath
        a=file(keyPath).read()
        key = a.split(',')
        key=[k.strip("\'") for k in key]
        key=[k.strip(" \'") for k in key]
        self.key = key
        self.conn = S3Connection(self.key[0], self.key[1])

    def getFileAgeMinutes(self, filekey):

        # get string date this file was last modified on S3
        lm = filekey.last_modified

        # convert this string into year,month,day,hr,mn,sec values to match time.gmtime
        monthList=list(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])
        monthDay=np.array([31,28,31,30,31,30,31,31,30,31,30,31])
        lmlist=lm.split()
        lm_year = int(lmlist[3])
        lm_day = int(lmlist[1])
        lm_mon = monthList.index(lmlist[2])
        lm_yday = monthDay.cumsum()[lm_mon-1] + lm_day
        timestr1 = lmlist[4]
        timestr2 = timestr1.partition(':')
        timestr3 = timestr2[2].partition(':')
        lm_hour = int(timestr2[0])
        lm_min = int(timestr3[0])
        lm_sec = int(timestr3[2])
        timeModSec = (3600*24*365*lm_year) + (3600*24*lm_yday) + (3600*lm_hour) + (60*lm_min) + (lm_sec)

        # compare time now with time file modified to get file age
        timeNow = time.gmtime()
        timeNowSec = (3600*24*365*timeNow[0]) + (3600*24*timeNow[7]) + (3600*timeNow[3]) + (60*timeNow[4]) + (timeNow[5])
        ageSec = timeNowSec - timeModSec
        ageMin =ageSec/60.

        return(ageMin)

    def uploadDirectoryAsBucket(self, bucketName,directoryPath,uploadConstituentFiles,overwriteContent):

        '''
        Allows simple copying of a local directory (and optionally its constituesnt files)to S3 as
        a bucket of the same name containing files of the same name.
    
        params to pass:
        bucketName              : (string) name to give bucket when it is created
        directoryPath           : (string) full path of directory on local machine that will be copied
        uploadConstituentFiles  : (logical) do we want to upload the files in this directory as objects in the bucket?
        overwriteContent        : (logical) if a file already exists in the bucket do we want to overwrite it? if False then only new files in this directory will be copied to bucket
        '''
    
        # run checks on this directory path
        if (os.path.exists(directoryPath) != True) :
            raise RuntimeError, "Path "+directoryPath+" does not exist: EXITING!!!\n"

        if (os.path.isdir(directoryPath) != True) :
            raise RuntimeError, "Path "+directoryPath+" is not a directory: EXITING!!!\n"

        # make sure path does not end with a '/' to ensure split works
        if directoryPath[-1] == '/':
            directoryPath = directoryPath[slice(0,len(directoryPath)-1,1)]

        # seperate directory name from path
        pathsplit = os.path.split(directoryPath)
        Path = pathsplit[0]
        directoryName = pathsplit[1]

        # create the bucket
        bucket = self.conn.create_bucket(str(bucketName))

        # upload a metadata file containing the path of the origin file
        k = boto.s3.key.Key(bucket)
        k.key='bucketOrigin.txt'
        k.set_contents_from_string('hostname:'+str(gethostname())+' path:'+str(directoryPath))

        # optionally, upload all files in this directory to this bucket
        if uploadConstituentFiles==True:

            for fname in os.listdir(directoryPath):
        
                # define full local path+filename for this file
                filename = directoryPath+'/'+str(fname)

                # check this is actually a file and not a directory before continuing
                if (os.path.isfile(filename) != True) : continue
            
                # if we are not allowing overwriting of files in this bucket, check if this file already exists on S3 and if so skip overwrite
                if overwriteContent==False:
                    if (self.CheckFileExistsInBucket(directoryName,fname) == True) : continue

                # establish key object
                k = boto.s3.key.Key(bucket)

                # give this key the same name as the file
                k.key = str(fname)

                # pass this file to S3 using the key
                k.set_contents_from_filename(filename)

                # finally, check that this file made it to S3
                md5string = md5.new(file(filename).read()).hexdigest()
                if (self.CheckFileExistsInBucket(bucketName,fname,md5check = md5string) != True) :
                    raise RuntimeError, 'Final check revealed file "'+str(filename)+'" did not copy succesfully to S3 bucket "'+str(bucketName)+'"'


    def makeEmptyBucket(self, bucketName):

        '''
        Simply creates a new empty bucket with the specified name, checking that
        no bucket of the same name already exists.
    
        params to pass:
        bucketName              :(string) name to give bucket when it is created
        '''
 
        #ensure input is string
        bucketName=str(bucketName)

        # check this bucket does not already exist
        if (self.conn.lookup(bucketName) is not None):
            print 'WARNING!!! requested bucket "'+str(bucketName)+'" already exists on S3 !!!'
            
    
        try:
            # create bucket with given name
            bucket = self.conn.create_bucket(bucketName)
        except boto.exception.S3CreateError:
            cls, inst, tb = sys.exc_info()
            print 'WARNING!!! Failed to create bucket. Error message: \n%s'%inst.body
    
        # check bucket now exists
        if (self.conn.lookup(bucketName) is None):
            print 'WARNING!!! requested bucket "'+str(bucketName)+'" does not appear to have been made on  S3 !!!'
                
    
        return(0)


    def uploadFileToBucket(self, bucketName,filePath,overwriteContent,makeBucket,VERBOSE=True):

        '''
        Allows simple copying of a single local file to a specified bucket.
    
        params to pass:
        bucketName              : (string) name of bucket to send file
        filePath                : (string) full path of file on local machine that will be copied
        overwriteContent        : (logical) if an object of this name already exists in the bucket, do we want to overwrite?
        makeBucket              : (logical) if the specified bucket does not exist, do we want to make it?
        '''

        #ensure input is string
        bucketName=str(bucketName)
        filePath=str(filePath)

        # check this is actually a file and it exists before continuing
        if (os.path.exists(filePath) != True) :
            raise RuntimeError, 'Requested file "'+str()+'" cannot be found: EXITING!!'

        if (os.path.isfile(filePath) != True) :
            raise RuntimeError, 'Requested file "'+str()+'" to upload to bucket is not a file: EXITING!!'
            

        # check sepcified bucket  exists and optionally make it
        if (self.conn.lookup(bucketName) is None):
            if makeBucket==False:
                raise RuntimeError, 'Requested bucket "'+str(bucketName)+'" does not exist on  S3 and makeBucket==False: EXITING!!!'

            if makeBucket==True:
                temp=self.makeEmptyBucket(bucketName)


        # obtain filename from path
        fileName = os.path.split(filePath)[1]
        
        # if worried about overwriting check if file exists already and abort if it does
        if overwriteContent==False:
            if (self.CheckFileExistsInBucket(bucketName,fileName) == True) :
                print 'WARNING!!! file "'+str(fileName)+'" already exists in bucket "'+str(bucketName)+'" and overwriteContent==False!!!'
                

        # now go ahead and upload file to the bucket

        ## link to the bucket with same name as directory
        bucket = self.conn.get_bucket(bucketName)

        ## establish key object
        k = boto.s3.key.Key(bucket)

        ## give this key the same name as the file
        k.key = str(fileName)

        ## pass this file to S3 using the key
        k.set_contents_from_filename(filePath)
    
        # finally, check that this file made it to S3
        md5string = md5.new(file(filePath).read()).hexdigest()
        if (self.CheckFileExistsInBucket(bucketName,fileName,md5check = md5string) != True) :
            raise RuntimeError, 'Final check revealed file "'+str(filePath)+'" did not copy succesfully to S3 bucket '+str(bucketName)+': EXITING!!!'

        return(0)


    def isLOCALFILEIdenticalToS3FILE(self, bucketName,fileNameInBucket,localFilePath):

        '''
        Checks whther a local file and a file on S3 are identical, according to their md5 strings. Does all the necessary checks
        and returns a True/False accordingly
    
        params to pass:
        bucketName              : (string) name of bucket that file of interest is located in 
        fileNameInBucket        : (string) name of file of interest in the bucket
        localFilePath           : (logical) full path to local file of interest
        '''

        # check local file exists
        if(checkAndBuildPaths(localFilePath,VERBOSE=True,BUILD=False)==-9999): return(False)
    
        # get md5 string for local file
        md5string = md5.new(file(localFilePath).read()).hexdigest()

        ## check this bucket exits
        if (self.conn.lookup(bucketName) is None):
            print 'WARNING!!! requested bucket "'+str(bucketName)+'" does not exist on S3 !!!'
            return(False)

        ## check the file exists on this bucket    
        if(self.CheckFileExistsInBucket(bucketName,fileNameInBucket,VERBOSE=True)!=True): return(False)  

        ## get md5 string for this file in the bucket
        bucket = self.conn.get_bucket(bucketName)
        filekey=bucket.get_key(fileNameInBucket)
        md5_s3 = filekey.etag.strip(str('"'))

        # compare this to the passed md5 string
        if (md5string != md5_s3):
            raise RuntimeError, 'The md5 string of file "'+str(fileNameInBucket)+'" in bucket "'+str(bucketName)+'" does not match that of local file at "'+str(localFilePath)+'"  !!!!'

        # if these tests passed, then return True
        return(True)    


    def CheckFileExistsInBucket(self, bucketName,fileNameInBucket, md5check=None, maxAgeMins=None, VERBOSE=False):

        '''
        Checks whether a file of the specified name exists in the specified bucket. Various options:
        1. md5check=None, maxAgeMins=None  = simply checks by filename
        2. maxAgeMins=float(minutes)  = checks that file exists and is younger than maxAgeMins
        2. md5check=str(md5str)  = checks that file exists and has identical md5 string to that passed by md5check
    
        params to pass:
        bucketName              : (string) name of bucket that file of interest is located in 
        fileNameInBucket        : (string) name of file of interest in the bucket
        md5check                : (string) an md5 string - if passed, will check that file in bucket has identical string
        maxAgeMins                : (float) if passed, will check that file in bucket is younger (since last modified) than this age in minutes
        '''
    
        # check this bucket exits
        if (self.conn.lookup(bucketName) is None):
            print 'WARNING!!! requested bucket "'+str(bucketName)+'" does not exist on S3 OR the connection failed using these access keys!!!'
            return(False)
    
        # check this file exists within this bucket
        bucket = self.conn.get_bucket(bucketName)
        keylist=[]
        rs=bucket.list()
        for key in rs:
            keylist.append(str(key.name))
    
        if (keylist.count(fileNameInBucket)==0) :
            if VERBOSE==True: print 'WARNING!!! file "'+str(fileNameInBucket)+'" not found in bucket "'+str(bucketName)+'"'
            return(False)
        
        # optionally check that the file was updated within the specified time
        if maxAgeMins is not None:
    
            filekey=bucket.get_key(fileNameInBucket)
            fileAge = self.getFileAgeMinutes(filekey)
        
            if fileAge>maxAgeMins:
                if VERBOSE==True: print 'WARNING!!! file "'+str(fileNameInBucket)+'" is older ('+str(fileAge)+' mins) than maxAgeMins ('+str(maxAgeMins)+' mins)'
                return(False)

        # optionally check that the file in the bucket has the same md5 string as that passed (e.g originating from a local file to check is identical)
        if md5check is not None:
       
            # get md5 string for this file in the bucket
            filekey=bucket.get_key(fileNameInBucket)
            md5_s3 = filekey.etag.strip(str('"'))

            # copmare this to the passed md5 string
            if (md5check != md5_s3):
                raise RuntimeError, 'The md5 string of file "'+str(fileNameInBucket)+'" in bucket "'+str(bucketName)+'" does not match that passed !!!!'
    
        # if these tests passed, then return True
        return(True)


    def downloadFileFromBucket(self, bucketName,fileNameInBucket,filePathAtDestination,overwriteContent,makeDirectory,VERBOSE=True):

        '''
        Downloads a single file from a bucket to a local directory
    
        params to pass:
        bucketName              : (string) name of bucket in which file of interest is lcoated
        fileNameInBucket        : (string) name of file of interest in bucket
        filePathAtDestination   : (string) full path - including filename itself - of the file once it has been downloaded
        overwriteContent        : (logical) if the specified target file already exists locally, do we overwrite?
        makeDirectory           : (logical) if the specified target file path includes new directories, should we make these?
        '''

        # check file exists in bucket
        if (self.CheckFileExistsInBucket(bucketName,fileNameInBucket,VERBOSE=True) != True) : 
            raise RuntimeError, 'File "'+str(fileNameInBucket)+'" does not exist in bucket: will not download requested file !!!'

        # if we are not overwriting, then check if file alrady exists locally : warn and abort download if it does
        if overwriteContent==False:
            if (os.path.exists(filePathAtDestination)==True):
                warnings.warn ('File "'+str(filePathAtDestination)+'" already exists and overwriteContent==False: will not download requested file !!!' )
            
        # if we are overwriting, check that existing file is not actually a directory
        if overwriteContent==True:
            if(os.path.isdir(filePathAtDestination)==True):
                raise RuntimeError, 'A directory ("'+str(fileNameInBucket)+'") exists at path "'+str(filePathAtDestination)+'" with same name as file trying to download: EXITING!!'

        # if we are making the local directory in which to copy this file, use checkAndBuildPaths to ensure it exists
        if makeDirectory==True:
            # first remove filename from file path to leave just path to directory
            fpathTrunc = filePathAtDestination.rpartition('/')[0]
            checkAndBuildPaths (fpathTrunc,VERBOSE=True,BUILD=True)

        bucket = self.conn.get_bucket(bucketName) 

        # establish key object
        filekey=bucket.get_key(fileNameInBucket)

        # pass the contents of file on s3 to the local file
        filekey.get_contents_to_filename(filePathAtDestination)

        # finally, check that this file made it from S3 to local destination

        ## first check there is even a file of this name at local destination
        if(os.path.exists(filePathAtDestination)!= True):
            raise RuntimeError, 'Final check revealed file "'+str(filePathAtDestination)+'" did not copy succesfully from S3 file "'+str(fileNameInBucket)+'" in bucket "'+str(bucketName)+'"'
            

        ## then check the md5 keys match
        md5_s3 = filekey.etag.strip(str('"'))
        md5string = md5.new(file(filePathAtDestination).read()).hexdigest()

        if(md5string != md5_s3):
            raise RuntimeError, 'Final check revealed file "'+str(filePathAtDestination)+'" did not copy succesfully from S3 file "'+str(fileNameInBucket)+'" in bucket "'+str(bucketName)+'"'
            


    def downloadBucketContents(self, bucketName,targetDirectoryPath,overwriteContent,VERBOSE=True):

        '''
        Downloads contents of an entire bucket to a specified local file.
    
        params to pass:
        bucketName              : (string) name of bucket of interest  
        targetDirectoryPath     : (string) path to target directory. If this includes new directories, these will be built if possible
        overwriteContent        : (logical) if the specifid pathis to an existing directory, and there are existing files with the same name as those in the bucket, do we overwrite?
        '''
    
        # check bucket exists on S3
        if (self.conn.lookup(bucketName) is None):
            print 'WARNING!!! requested bucket "'+str(bucketName)+'" does not exist on S3 !!!'
            
        
        # check target local directory exists and if not then build it        
        if(checkAndBuildPaths(targetDirectoryPath,BUILD=True)==-9999):
            raise RuntimeError, 'Problem building target directory "'+str(targetDirectoryPath)+'" : EXITING!!!'
            

        # get list of files already in target directory
        existinglocalfiles = os.listdir(targetDirectoryPath)

        # loop through all files in the bucket
        bucket = self.conn.get_bucket(bucketName)
        rs=bucket.list()
        for key in rs:
    
            # if not overwriting, check no file exists in local directory with same name as this file
            if overwriteContent==False:
                if (existinglocalfiles.count(str(key.name))>0):
                    if VERBOSE==True: print 'WARNING!!! file "'+str(key.name)+'" already present in local directory "'+str(targetDirectoryPath)+'" and overwriteContent==False '
                    continue

            # if we are overwriting, check that existing file is not actually a directory
            if overwriteContent==True:
                if(os.path.isdir(targetDirectoryPath+str(key.name))==True):
                    raise RuntimeError, 'A directory ("'+str(key.name)+'") exists at path "'+str(targetDirectoryPath)+'" with same name as file trying to download: EXITING!!'
                    

        
            # build full target filepath
            if targetDirectoryPath[-1] != '/': targetDirectoryPath = targetDirectoryPath+'/'
            filePathAtDestination = targetDirectoryPath+str(key.name)

            # now copy this file from S3 bucket to local directory
            key.get_contents_to_filename(filePathAtDestination)        
        
            # check file has made it to destination
        
            ## first check there is even a file of this name at local destination
            if(os.path.exists(filePathAtDestination)!= True):
                raise RuntimeError, 'Final check revealed file "'+str(filePathAtDestination)+'" did not copy succesfully from S3 file "'+str(key.name)+'" in bucket "'+str(bucketName)+'"'
                

            ## then check the md5 keys match
            md5_s3 = key.etag.strip(str('"'))
            md5string = md5.new(file(filePathAtDestination).read()).hexdigest()

            if(md5string != md5_s3):
                raise RuntimeError, 'Final check revealed file "'+str(filePathAtDestination)+'" did not copy succesfully from S3 file "'+str(key.name)+'" in bucket "'+str(bucketName)+'"'

    def queryRealizationsInBucket(self, relBucket,relPath,VERBOSE=True):

        '''
        Queries a specified bucket for realisation files and returns dictionary with N realisations, and lists of start and end realisation numbers
    
        params to pass:
        relBucket     : (string) name of S3 bucket containing realisations
        relPath       : (string) a generic filename for the realisatios in this bucket (same format as that in extract params, with FILESTARTREL
                        and FILEENDREL suffixes denoting the firs and last realisatoin couintained in each realisation filepath to target directory. If this includes new directories, these will be built if possible
        '''

        # define reference filepath for later use - removing the .hdf5 suffix                   
        TEMPrelPath = relPath.rpartition('.')[-3]

        # check bucket exists on S3
        if (self.conn.lookup(relBucket) is None):
            print 'WARNING!!! requested bucket "'+str(relBucket)+'" does not exist on S3 !!!'
            return(-9999)

        # connect to bucket of interest and define list of filenames therein
        bucket = self.conn.get_bucket(relBucket)
        keylist=[]
        rs=bucket.list()
        for key in rs:
            keylist.append(str(key.name))
        NfilesInBucket = len(keylist)

        Nrealisations = 0
        Nfiles = 0
        StartRelList = []
        EndRelList = []

        # loop thorugh filenames in bucket, check they are a realisatoin file, and if so extract start and end realistaion info
        for i in xrange(0,NfilesInBucket):

            # get the ith filename in the bucket
            fileN=keylist[i]
            
            # first check it is an hdf5 file
            if fileN.rpartition('.')[-1]=='hdf5':
                
                # truncate this filename to remove extension
                TEMPPath = fileN.rpartition('.')[-3]
            
                # compare this filename to the generic realisation filename (after removing the realisation-specific suffixes), if they match then assume this is a realisation file
                if (TEMPPath.split('_')[0:-2:1]==TEMPrelPath.split('_')[0:-2:1]):
                    
                    # extract start and end realisation numbers from file suffixes
                    StartRelList.append(TEMPPath.split('_')[-2])
                    EndRelList.append(TEMPPath.split('_')[-1])
                    
                    # increment counter of valid realisation files in this bucket
                    Nfiles+=1
                    
                    # and increment counter of nuber of individual realisations in this bucket (a file may have more than one realisation)
                    Nrealisations=Nrealisations +  int(TEMPPath.split('_')[-1]) - int(TEMPPath.split('_')[-2])                     

        # return dictionary with start and end realisation lists and number of realisations
        returnDict = {"Nfiles":Nfiles,"Nrealisations":Nrealisations,"StartRelList":StartRelList,"EndRelList":EndRelList}
        return returnDict

