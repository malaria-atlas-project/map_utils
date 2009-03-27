import sys
import time
import subprocess
import numpy as np


# sepcify some parameters
MAXJOBS = 5         # how many processes do we want running at a time
WAITINTERVAL = 5    # wait interval in seconds
VERBOSE = True      # messages or not


# two simmple functions to allow a method to be applied accross elements of a list
def applyPoll(sp):
    return(sp.poll())
    
def apply_is_None(sp):
    return(sp is None)


# initialise list to hold subprocess objects (containing info about each subprocess)
splist = []

# initialise counter for output messages
if VERBOSE: cnt = 0

# set off jobs
for i in xrange(0,20):

    # define command line syntax for this subprocess 
    args = (['python','/home/pwg/map_utils/map_utils/examplemulti_func.py',str(i),str(i*2)])

    # start this subprocess, and assign the subprocess object to the splist
    splist.append(subprocess.Popen(args))
    if VERBOSE:
        print 'sent job '+str(cnt)
        cnt=cnt+1

    # if number of jobs running has reached MAXJOBS, keep checking for jobs to finish before sending more
    while sum(map(apply_is_None,np.array(map(applyPoll,splist)))) >= MAXJOBS:
        time.sleep(WAITINTERVAL)
        if VERBOSE: print("waiting at time"+ str(time.time()))

# once all jobs have been dispatched, wait for all to finish before continuing
while sum(map(apply_is_None,np.array(map(applyPoll,splist)))) !=0:
    time.sleep(WAITINTERVAL)

# check for any jobs that did not execute successfully
sumSuccess = sum(np.array(map(applyPoll,splist))==0)
sumFail = sum(np.array(map(applyPoll,splist))>0)

if VERBOSE: print 'successful jobs: '+str(sumSuccess)+' of '+str(len(splist))
if sumFail!=0: print 'failed jobs: '+str(sumFail)+' of '+str(len(splist))
