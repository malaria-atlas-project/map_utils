# Author: Pete Gething
# Date: 5 March 2009
# License: Creative Commons BY-NC-SA
####################################

import os

#############################################################################################################################################

__all__ = ['checkAndBuildPaths']

def checkAndBuildPaths (fpath,VERBOSE=False,BUILD=False):

    # check file paths used as inputs to other functions.
    # BUILD==False: simply check whether a filepath exists - if not returns an error (-9999)
    # BUILD==True: will attempt to create the requested filepath by making new directories
    # but will fail and return error if cannot find the path root, or if the path looks like a file
    # rather than a directory

    # first, check whether file or directory exists
    if os.path.exists(fpath) == True:

        # if exists but is neither file nor directory..give error and exit
        if (os.path.isfile(fpath) == False) & (os.path.isdir(fpath) == False):
            print "WARNING!!! Object at "+fpath+" exists but is not a file or a directory\n"
            return(-9999) 

       # if  either file or directory, then return success after giving tailored confirmation message
        if VERBOSE==True :
            if os.path.isdir(fpath) == True : print "Directory "+fpath+" exists\n"
            if os.path.isfile(fpath) == True : print "File "+fpath+" exists\n"

        return(0)        

    # if file or directory does not exist
    if os.path.exists(fpath) == False:

        # if we are not building missing directories, just return error
        if BUILD==False:
            print "WARNING!!! Object at "+fpath+" does not exist - not building so check manually\n"
            return(-9999)

        # if we are building missing directories, first guess whether the desired path is to a directory or a file:

        # get last component of path, and define whether a file (recognised by having an extension) or a directory (no extension)
        #last = os.path.split(fpath)[-1]

        #if last == '':
        #    pathtype = "DIR"
        #elif last.find(".") == -1:
        #   pathtype = "DIR"
        #else:
        #    pathtype = "FILE"
        #    print "WARNING!!! Object at "+fpath+" does not exist - asked to build BUT THIS LOOKS LIKE A FILE - so check manually\n"
        #    return(-9999)

        # if happy its a directory, we can now start building the missing directories
        mkdir_errors = True
        splitpath=fpath
        if splitpath[-1]=='/': splitpath = splitpath[0:(len(splitpath)-1)]
        missingDirs=list()

        # loop back through path, listing direcotries that are missing, and checking that we can at least find a recognized root
        while os.path.exists(splitpath) == False :
            splitout = os.path.split(splitpath)
            splitpath = splitout[0]
            if (splitpath == '/') | (splitpath == ''):
                print "WARNING!!! the requested path "+str(fpath)+" has non-recognized root: EXITING\n"
                return(-9999)
            missingDirs.append(splitout[1])

        Nmissing = len(missingDirs)
        if VERBOSE == True:
           print "NOTICE: path to directory "+fpath+" is missing directories: "+str(missingDirs)+" ..attempting to build this path..\n"


        # now loop throgh each missing directory and attempt to build
        for i in xrange(0,Nmissing):
            if splitpath != '/' :
                splitpath = splitpath+'/'
            splitpath = splitpath+missingDirs[Nmissing-(i+1)]
            try:
                if VERBOSE ==True: print splitpath
                os.mkdir(splitpath)
            except OSError:
                print "WARNING!!!! could not build directory "+str(missingDirs[Nmissing-(i+1)])+" : EXITING\n"
                return(-9999)
            if VERBOSE == True:
                print "succesfully built directory "+str(missingDirs[Nmissing-(i+1)])+"\n"

        return(0)

#############################################################################################################################################
#temp = checkAndBuildPaths('/Home/pwg/mbg-world/extraction/CombinedOutput/test1/test2',VERBOSE= True,BUILD=True)



