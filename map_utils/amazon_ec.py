import boto
from subprocess import PIPE, STDOUT, Popen
import time
import numpy as np
import copy as cp

#__all__ = ['send_work', 'spawn_engines', 'stop_all_engines', 'map_jobs'] 

init_ssh_str = 'ssh -o "StrictHostKeyChecking=no" -i /amazon-keys/MAPPWG.pem'
init_scp_str = 'scp -o "StrictHostKeyChecking=no" -i /amazon-keys/MAPPWG.pem'
##################################################################################################################################################
def send_work(e, cmd, outToFile = None, outSuffix=None):
    """
    e: a boto Instance object (an Amazon EC2 instance)
    cmd: a string
    
    After the call, e.PendingJoblist will be a list of Popen instances. e.PendingJoblist.cmd will be a list of commands (cmd).
    """
    command_str = init_ssh_str + ' root@%s %s'%(e.dns_name, cmd)

    if outToFile is None:
        job = Popen(command_str, shell=True, stdout=PIPE, stderr=STDOUT)

    if outToFile is not None:
        if outSuffix is None:
           stdout = file(str(outToFile)+'stdout.txt','w')
           stderr = file(str(outToFile)+'stderr.txt','w')
           
        if outSuffix is not None:
           stdout = file(str(outToFile)+'stdout_'+str(e).rpartition(':')[-1]+'_'+str(outSuffix)+'.txt','w')
           stderr = file(str(outToFile)+'stderr_'+str(e).rpartition(':')[-1]+'_'+str(outSuffix)+'.txt','w')           
        
        job = Popen(command_str, shell=True, stdout=stdout, stderr=stderr) 

    job.cmd = cmd
    e.PendingJoblist.append(job) 
##################################################################################################################################################
def stop_all_engines():
    """
    Shuts down ALL Amazon EC2 instances we own!
    """
    conn = boto.connect_ec2()
    for r in conn.get_all_instances():
        r.stop_all()
##################################################################################################################################################
def spawn_engines(N_engines):
    """
    Starts up N_engines engines using the image with scipy, etc. on it.
    """
    conn = boto.connect_ec2()
    r = conn.run_instances('ami-88e80fe1', min_count=N_engines, max_count=N_engines, security_groups=['MAP'], instance_type='m1.lcmde')
    print 'Starting %s'%r.instances
##################################################################################################################################################
def map_jobs_APP_HOLD(cmds, init_cmds=None, upload_files=None, interval=10, shutdown=True):    
    """
    cmds: list of strings that can be executed from the shell.
    
    Optional arguments:
        upload_files: list of paths.
          Will be uploaded to each instance before any init_cmds or cmds
          are sent to it.
        init_cmds: list of strings that can be executed from the shell.
          Will be executed once, in order, on each instance before any cmds
          are sent to it.
        interval: integer. Delay in seconds between polling instances.
        shutdown: boolean. Whether to shut down instances that are not needed.
          If True, all instances will be terminating by the time function returns.
          
    Returns a list of (cmd, output) tuples. Output is everything the process wrote
    to stdout and stderr... but there won't be anything in stderr, because only
    successful exits get written out. 
    """
    returns = []
    
    conn = boto.connect_ec2()
    r = conn.get_all_instances()[-1]
    print 'Extant engines are %s'%r.instances
        
    spawning_engines = [e for e in r.instances]
    running_engines = []
    done = False
    retcode = None
    
    while True:
        print '\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
        print "Gotta check my fly-paper... see what's stickin."
    
        # Watch engines to see when they come alive.
        for e in spawning_engines:
            if e.update()==u'running':
                print '\n%s is up'%e
                e.job = None
                spawning_engines.remove(e)
                running_engines.append(e)
                if upload_files is not None:
                    print '\n\tUploading files to %s'%e
                    for upload_file in upload_files:
                        print '\t'+upload_file
                        p = Popen(init_scp_str +  ' %s root@%s:%s'%(upload_file, e.dns_name, upload_file), shell=True, stdout=PIPE,stderr=STDOUT)
                        retval = p.wait()
                        if retval:
                            raise ValueError, 'Upload failed! Output:\n' + p.stdout.read()
                if init_cmds is not None:
                    print '\n\tExecuting initial commands on %s'%e
                    for init_cmd in init_cmds:
                        print '\t$ %s'%init_cmd
                        p = Popen(init_ssh_str + ' root@%s '%e.dns_name+ init_cmd, shell=True, stdout=PIPE, stderr=STDOUT)
                        while p.poll() is None:
                            print '\t\tWaiting for %i...'%p.pid
                            time.sleep(10)
                        retval = p.poll()                    
                        if retval:
                            raise ValueError, 'Initial command failed! Output:\n' + p.stdout.read()
                        print '\tSuccessful.'    

        N_running = 0
        for e in running_engines:
            # See if previous work is done
            if e.job is not None:
                retcode = e.job.poll()

                if retcode is not None:
            
                    print '\n\t%s has completed\n\t$ %s\n\twith code %i'%(e,e.job.cmd,retcode)
                    if retcode>0:
                        print '\n\tAdding\n\t$ %s\n\tback onto queue because %s fucked it up, code %i. Message:\n'%(e.job.cmd, e, retcode)
                        for line in e.job.stdout:
                            print line
                        cmds.append(e.job.cmd)
                    else:
                        returns.append((e.job.cmd, e.job.stdout.read()))
                        
                else:
                    N_running += 1
        
            # In event of fault, move e back to spawning list.
            if e.update()!=u'running':
                running_engines.remove(e)
                spawning_engines.append(e)
        
            # Send work    
            elif (e.job is None or retcode is not None) and not done:
                if len(cmds) == 0:
                    print 'No jobs remaining in queue'
                    done = True
                else:
                    cmd=cmds.pop(0)
                    print '\n\tSending\n\t$ %s\n\tto %s'%(cmd,e)
                    send_work(e, cmd)
                    N_running += 1

            # Kill the engine
            if done and shutdown:
                print 'Stopping %s'%e
                e.stop()

        if done and N_running == 0:
            print 'All jobs complete!'
            break
        print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'        
        time.sleep(interval)
    
    if shutdown:
        r.stop_all()
    return returns
##################################################################################################################################################
def getReservationIndex (r,reservationID):

    Nreservations = len(r)

    for i in xrange(0,Nreservations):
        resID = str(r[i])
        resID=resID.partition('Reservation:')[2]
        if resID == reservationID:
            return(i)
        else:
            continue

    print 'ERROR!!! Could not find reservation "'+str(reservationID)+'" : EXITING!!!'
###########################################################################################################################
def queryJobsOnInstance(splist):

    sumRunning = 0
    sumFinished = 0
    FinishedJobIndex = []
    Njobs = len(splist)
    for i in xrange(0,Njobs):
        job = splist[i]
        jobstat = job.poll()
        if jobstat is None:
            sumRunning = sumRunning +1
        if jobstat is not None:
            sumFinished = sumFinished +1
            FinishedJobIndex.append(i)

    # return dictionary
    return({'sumRunning':sumRunning,'sumFinished':sumFinished,'FinishedJobIndex':FinishedJobIndex}) 
###########################################################################################################################
##RESERVATIONID;NINSTANCES;MAXJOBSPERINSTANCE;cmds=CMDS;init_cmds=INITCMDS;upload_files=UPLOADFILES;interval=20;shutdown=False
def map_jobs(RESERVATIONID, NINSTANCES, MAXJOBSPERINSTANCE, MAXJOBTRIES,cmds, init_cmds=None, upload_files=None, interval=10, shutdown=True,STDOUTPATH=None):    
    """

    RESERVATIONID       : (str) label identifying the EC2 reservation we are dealing with
    NINSTANCES          : (int) number iof instances available on this reservation
    MAXJOBSPERINSTANCE  : (int) number of jobs that will be run simultaneiously on each instance
    MAXJOBTRIES         : (int) maximum number of time each individual job will be attempted before killing it
    cmds                : (list, str) list of strings that can be executed from the shell.
    
    Optional arguments:
        upload_files    : (list,str) list of paths -  Will be uploaded to each instance before any init_cmds or cmds are sent to it.
        init_cmds       : (list,str) list of strings that can be executed from the shell. Will be executed once, in order, on each instance before any cmds are sent to it.
        interval        : (int). Delay in seconds between polling instances.
        shutdown        : (bool) Whether to shut down instances that are not needed.  If True, all instances will be terminating by the time function returns.
        STDOUTPATH:     : (str) path to local directory which will house stdout and stderr files
          
    """
    returns = []

    conn = boto.connect_ec2()
    r_all = conn.get_all_instances()
    r = r_all[getReservationIndex(r_all,RESERVATIONID)]
    
    print 'Extant engines are %s'%r.instances
    
    # check the number of instances found is same or more than that asked for
    if (len(r.instances) < NINSTANCES):
        raise RuntimeError, 'Asked for '+str(NINSTANCES)+' instances but found only '+str(len(r.instances))+' on reservation '+str(RESERVATIONID)+': EXITING map_jobs_PWG!!!'

    spawning_engines = [e for e in r.instances]
    running_engines = []
    failedJobCmds = np.array([])
    failedJobCount = np.array([])

    NjobsRunning=0
    TotalCompleteOK = 0
    TotalFailures = 0

    while True:
        print '\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
        print str(len(spawning_engines))+' instances spawning;   '+str(len(running_engines))+' instances running'
        print 'Job Status:    '+str(NjobsRunning)+' running;    '+str(TotalCompleteOK)+' completed successfully;    '+str(TotalFailures)+' failures.'
    
        # Watch engines to see when they come alive.
        print 't1'
        for e in spawning_engines:
            if e.update()==u'running':
                print '\n%s is up'%e
                print 't2'
                e.PendingJoblist = []
                print 't3'
                spawning_engines.remove(e)
                print 't4'
                running_engines.append(e)
                print 't5'
                if upload_files is not None:
                    print 't6'
                    print '\n\tUploading files to %s'%e
                    print 't7'
                    for upload_file in upload_files:
                        print 't8'
                        print '\t'+upload_file
                        print 't9'
                        #p = Popen(init_scp_str +  ' %s root@%s:%s'%(upload_file, e.dns_name, upload_file.split("/")[-1]), shell=True, stdout=PIPE,stderr=STDOUT)
                        stdout = file(str(STDOUTPATH)+'stdout_upload_'+str(e).rpartition(':')[-1]+'_'+str(upload_file).rpartition('/')[-1]+'.txt','w')
                        print 't10'
                        stderr = file(str(STDOUTPATH)+'stderr_upload_'+str(e).rpartition(':')[-1]+'_'+str(upload_file).rpartition('/')[-1]+'.txt','w') 
                        print 't11'
                        p = Popen(init_scp_str +  ' %s root@%s:%s'%(upload_file, e.dns_name, upload_file.split("/")[-1]), shell=True, stdout=stdout,stderr=stderr)
                        print 't11'

                        retval = p.wait()
                        print 't12'
                        if retval:
                            raise ValueError, 'Upload failed! Output:\n' + p.stdout.read()
                if init_cmds is not None:
                    print 't13'
                    print '\n\tExecuting initial commands on %s'%e
                    for init_cmd in init_cmds:
                        print 't14'
                        print '\t$ %s'%init_cmd
                        #p = Popen(init_ssh_str + ' root@%s '%e.dns_name+ init_cmd, shell=True, stdout=PIPE, stderr=STDOUT)
                        stdout = file(str(STDOUTPATH)+'stdout_initial_'+str(e).rpartition(':')[-1]+'_'+str(init_cmd).rpartition('/')[-1].strip('"')+'.txt','w')
                        print 't15'
                        stderr = file(str(STDOUTPATH)+'stderr_initial_'+str(e).rpartition(':')[-1]+'_'+str(init_cmd).rpartition('/')[-1].strip('"')+'.txt','w') 
                        print 't16'
                        p = Popen(init_ssh_str + ' root@%s '%e.dns_name+ init_cmd, shell=True, stdout=stdout, stderr=stderr)
                        print 't17'
                        while p.poll() is None:
                            print '\t\tWaiting for %i...'%p.pid
                            print 't18'
                            time.sleep(10)
                            print 't19'
                        retval = p.poll()
                        print 't20'
                        if retval:
                            raise ValueError, 'Initial command failed! Output:\n' + p.stdout.read()
                        print '\tSuccessful.'

        # loop through running instances and deal with jobs that have finished (succesfully or otherwise)
        NjobsRunning=0

        for e in running_engines:
        
            # In event of fault, move e back to spawning list and move this loop on to next instance
            if e.update()!=u'running':
                running_engines.remove(e)
                spawning_engines.append(e)
                continue

            # how many jobs are running on this instance, what are their statuses, and where can we find them on on e.PendingJoblist?
            JobsOnInstanceDict=queryJobsOnInstance(e.PendingJoblist)

            # if we have one or more that have newly finished on this instance:
            if(JobsOnInstanceDict['sumFinished']>0):
                
                #loop through them (in descending order so list can shorten as we go), check their return status, and act accordingly
                tempindex = cp.deepcopy(JobsOnInstanceDict['FinishedJobIndex'])
                tempindex.sort(reverse=True)
                for i in tempindex:
            
                    job=e.PendingJoblist[i]
                    job.status = job.poll()
                                   
                    print '\n\t%s has completed\n\t$ %s\n\twith code %i'%(job,job.cmd,job.status)

                    # if a non-zero return code then this job had a problem and needs adding back to job list             
                    if job.status>0:
                        
                        TotalFailures+=1
                        
                        # before adding back to list, check if this job has already been tried more than MAXJOBTRIES times
                        failedJobIndex = failedJobCmds==job.cmd
                        if(type(failedJobIndex)==type(False)): failedJobIndex=np.array([failedJobIndex])
                        
                        # is this cmd already on list of shame?
                        if failedJobIndex.any()==True:

                            # if already failed MAXJOBTRIES times, then do not return to queue
                            if failedJobCount[failedJobIndex]>=MAXJOBTRIES:
                                print '\n\tCommand\t$ %s\n\t from %s received error code %i BUT NOT ADDED BACK TO QUEUE BECAUSE HAS NOW FAILED %i TIMES.\n'%(job.cmd, job, job.status, MAXJOBTRIES)

                            # if not yet failed MAXJOBTRIES times, then return to queue for another go and increment fail count
                            if failedJobCount[failedJobIndex]<MAXJOBTRIES:
                                print '\n\tAdding\n\t$ %s\n\tback onto queue because %s received error code %i.\n'%(job.cmd, job, job.status)
                                cmds.append(job.cmd)
                                failedJobCount[failedJobIndex]+=1

                        # if this cmd not yet on  list of shame (and if MAXJOBTRIES greater than one) then add it, along with failure counter, after adding job back to list
                        else:
                            if MAXJOBTRIES==1:
                                print '\n\tCommand\t$ %s\n\t from %s received error code %i BUT NOT ADDED BACK TO QUEUE BECAUSE HAS NOW FAILED %i TIMES.\n'%(job.cmd, job, job.status, MAXJOBTRIES)
                                
                            else:
                                print '\n\tAdding\n\t$ %s\n\tback onto queue because %s received error code %i.\n'%(job.cmd, job, job.status)
                                cmds.append(job.cmd)
                                failedJobCmds = np.concatenate((failedJobCmds,np.array([job.cmd])))
                                failedJobCount = np.concatenate((failedJobCount,np.array([1])))

                    # if a zero return code then this job has finished succesfully and can add its standard outut to list for return
                    else:
                        TotalCompleteOK+=1 
                        if job.stdout is not None: returns.append((job.cmd, job.stdout.read()))
                        
                    # whether finished succesfully or otherwise, this job can now be removed from PendingJoblist
                    temp = e.PendingJoblist.pop(i)

            # if no more jobs in queue AND if there are now no more jobs either running or recently finished on this instance AND shutdown==True, then kill it
            if((JobsOnInstanceDict['sumRunning']==0) & (len(cmds)==0) & shutdown==True):
                print 'Stopping %s'%e
                e.stop()
                running_engines.remove(e)
                continue

            # else if we have less jobs running on this instance than are permitted (and if there are jobs waiting to be started), then send more jobs:
            NjobsRunningThisInstance =  JobsOnInstanceDict['sumRunning']
            NjobsRunning = NjobsRunning + NjobsRunningThisInstance
            if( (NjobsRunningThisInstance<MAXJOBSPERINSTANCE) & (len(cmds)>0) ) :
                NspareJobs = min ((MAXJOBSPERINSTANCE-NjobsRunningThisInstance),len(cmds))
                for j in xrange(0,NspareJobs):
                    cmd=cmds.pop(0)
                    print '\n\tSending\n\t$ %s\n\tto %s'%(cmd,e)
                    if STDOUTPATH is not None: send_work(e, cmd, outToFile=STDOUTPATH, outSuffix = str(time.time()))
                    else: send_work(e, cmd)
                    NjobsRunning = NjobsRunning +1
                
        # if no jobs still in queue and none still running then assume jobs are finished..
        if ((NjobsRunning == 0) & (len(cmds)==0)):
        
            # If shutdown==True check that all instances have been shut down
            if ( (shutdown==True) & (len(running_engines)!=0) ):
                print "WARNING!!! no jobs running or in queue but following instances still alive, so shuting down all in this reservation\n"
                print running_engines
                r.stop_all()

            # exit loop
            print 'All jobs complete!'
            break


        # now wait a specified interval before going again through a loop of the instances
        print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'        
        time.sleep(interval)

    return returns
###################################################################################################################################################
#if __name__ == '__main__':
#    # How many processes to spawn?
#    # N_engines = 2
#    N_jobs = 2
#    iter_per_job = 2
#    cmds = ['screen ipython amazon_joint_sim.py %i %i %i'%(i,iter_per_job,N_jobs) for i in xrange(N_jobs)]
#    returns = map_jobs(cmds, 
#                shutdown=True, 
#                upload_files=['amazon_joint_sim.py','/home/pwg/mbg-world/mbgw-scripts/cloud_setup.sh','/home/pwg/mbg-world/mbgw-scripts/s3code.txt'], 
#                init_cmds=['bash /root/cloud_setup.sh'], 
#                interval=20)    
#    
#    # cmds = ['python boto_upload.py %i'%i for i in xrange(N_jobs)]
#    # returns = map_jobs(cmds, shutdown=False, upload_files=['boto_upload.py','cloud_setup.sh'], init_cmds=['bash /root/cloud_setup.sh', 'apt-get install python-boto'], interval=2)




