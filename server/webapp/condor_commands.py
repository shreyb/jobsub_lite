import logger
import traceback
import math
import platform
import os
import errno
import zipfile
import time
import sys
import mimetypes
import base64
import json
import subprocessSupport
import socket
import re


if platform.system() == 'Linux':
    try:
        import htcondor as condor
        import classad
    except:
        logger.log('Cannot import htcondor. Have the condor'+\
                ' python bindings been installed?')

def ui_condor_userprio():
    all_users, cmd_err = subprocessSupport.iexe_cmd(
            'condor_userprio -allusers')
    return all_users

def ui_condor_status_totaljobs():
    all_jobs, cmd_err = subprocessSupport.iexe_cmd(
            'condor_status -schedd -af name totaljobads')
    return all_jobs

def ui_condor_queued_jobs_summary():
    all_queued1, cmd_err = subprocessSupport.iexe_cmd(
            'condor_status -submitter -wide')
    tmp=all_queued1.split('\n')
    idx = [i for i, item in enumerate(tmp) \
            if re.search('^.\s+RunningJobs', item)]
    del tmp[idx[0]:]
    all_queued1='\n'.join(tmp)
    all_queued2, cmd_err = subprocessSupport.iexe_cmd(
            '/opt/jobsub/server/webapp/ifront_q.sh')
    all_queued="%s\n%s"%(all_queued1,all_queued2)
    return all_queued


def condor_header(inputSwitch=None):
    if inputSwitch=='long':
        hdr=''
    elif inputSwitch=='dags':
        hdr="JOBSUBJOBID                           USER     DAG_INFO     SUBMITTED     RUN_TIME   ST PRI SIZE CMD\n"
    else:
        hdr="JOBSUBJOBID                           USER          SUBMITTED     RUN_TIME   ST PRI SIZE CMD\n"
    return hdr

def condor_format(inputSwitch=None):

    if inputSwitch=='long':
        fmt = " -l "
    elif inputSwitch=='dags':
        fmt="""-format '%-37s'  'regexps("((.+)\#(.+)\#(.+))",globaljobid,"\\3@\\2 ")' -format '%-8s' 'ifthenelse(dagmanjobid =?= UNDEFINED, string(owner),strcat("|-"))' -format '%-14s ' 'ifthenelse(dagmanjobid =!= UNDEFINED, string(dagnodename),ifthenelse(DAG_NodesDone =!= UNDEFINED, strcat(string("dag, "),string(DAG_NodesDone),string("/"),string(DAG_NodesTotal),string(" done")),"") )' -format '%-11s ' 'formatTime(QDate,"%m/%d %H:%M")' -format '%3d+' 'int(RemoteUserCpu/(60*60*24))' -format '%02d:' 'int((RemoteUserCpu-(int(RemoteUserCpu/(60*60*24))*60*60*24))/(60*60))' -format '%02d:' 'int((RemoteUserCpu-(int(RemoteUserCpu/(60*60))*60*60))/(60))' -format '%02d ' 'int(RemoteUserCpu-(int(RemoteUserCpu/60)*60))' -format '%-2s ' 'ifThenElse(JobStatus==0,"U",ifThenElse(JobStatus==1,"I",ifThenElse(TransferringInput=?=True,"<",ifThenElse(TransferringOutput=?=True,">",ifThenElse(JobStatus==2,"R",ifThenElse(JobStatus==3,"X",ifThenElse(JobStatus==4,"C",ifThenElse(JobStatus==5,"H",ifThenElse(JobStatus==6,"E",string(JobStatus))))))))))' -format '%-3d ' JobPrio -format '%-4.1f ' ImageSize/1024.0 -format '%-30s' 'regexps(".*\/(.+)",cmd,"\\1")' -format '\\n' Owner """ 
    else:
        fmt=""" -format '%-37s' 'regexps("((.+)\#(.+)\#(.+))",globaljobid,"\\3@\\2 ")'  -format '%-14s ' Owner -format '%-11s ' 'formatTime(QDate,"%m/%d %H:%M")' -format '%3d+' 'int(RemoteUserCpu/(60*60*24))' -format '%02d:' 'int((RemoteUserCpu-(int(RemoteUserCpu/(60*60*24))*60*60*24))/(60*60))' -format '%02d:' 'int((RemoteUserCpu-(int(RemoteUserCpu/(60*60))*60*60))/(60))' -format '%02d ' 'int(RemoteUserCpu-(int(RemoteUserCpu/60)*60))' -format '%-2s ' 'ifThenElse(JobStatus==0,"U",ifThenElse(JobStatus==1,"I",ifThenElse(JobStatus==2,"R",ifThenElse(JobStatus==3,"X",ifThenElse(JobStatus==4,"C",ifThenElse(JobStatus==5,"H",ifThenElse(JobStatus==6,"E",string(JobStatus))))))))' -format '%-3d ' JobPrio -format '%-4.1f ' ImageSize/1024.0 -format '%-30s ' 'regexps(".*\/(.+)",cmd,"\\1")' -format '\\n' Owner """
    return fmt



def munge_jobid( theInput=None):
    header=['ID',' ',' ',' ','OWNER','SUBMITTED','RUN_TIME','ST','PRI','SIZE','CMD']
    if theInput==None:
        return None
    linput=theInput.split('\n')
    loutput=[]
    loutput.append("\t".join(header))
    for line in linput:
        if line=='':
            continue
        llout=line.split()
        loutput.append("\t".join(llout))
    return "\n".join(loutput)


def constructFilter( acctgroup=None, uid=None, jobid=None):
    if acctgroup=='None':
        acctgroup=None
    if uid=='None':
        uid=None
    if jobid=='None':
        jobid=None
    lorw = ' '
    if acctgroup is None:
        ac_cnst = 'True'
    else:
        ac_cnst = """regexp("group_%s.*",AccountingGroup)"""%acctgroup

    if uid is None:
        usr_cnst = 'True'
    else:
        usr_cnst = 'Owner=="%s"'%uid

    if jobid is None:
        job_cnst = 'True'
    elif jobid.find('@')>=0:
        x=jobid.split('@')
        l=len(x)
        clusterid=x[0]
        host='@'.join(x[1:])
        if clusterid.find('.')<0:
            clusterid=clusterid+'.0'
        job_cnst = """regexp("%s#%s.*",GlobalJobId)""" %(host,clusterid)
    else:
        lorw = ' '
        job_cnst = 'ClusterID==%d'%(math.trunc(float(jobid)))
    filter = " %s -constraint '%s && %s && %s' "%(lorw, ac_cnst,usr_cnst,job_cnst)
    return filter

def ui_condor_history(filter=None,format=None):
    hdr=condor_header(format)
    if filter is None:
        cmd = 'condor_history %s' % condor_format(format)
    else:
        if "GlobalJobId" in filter:
            filter = "%s %s" % (filter, "-match 1")
        cmd = 'condor_history %s %s' % (condor_format(format),filter)
    all_jobs, cmd_err = subprocessSupport.iexe_cmd(cmd)
    return hdr + all_jobs

def ui_condor_q(filter=None,format=None):

    hdr=condor_header(format)
    fmt=condor_format(format)
    if filter is None:
        cmd = 'condor_q -g %s ' % fmt
    else:
        cmd = 'condor_q -g %s %s' % (fmt,filter)

    try:
        all_jobs, cmd_err = subprocessSupport.iexe_cmd(cmd)
        #logger.log("cmd=%s"%cmd)
        #logger.log("rslt=%s"%all_jobs)
        return hdr + all_jobs
    except:
        tb = traceback.format_exc()
        logger.log(tb)
        no_jobs="All queues are empty"
        if len(re.findall(no_jobs, tb)):
            return no_jobs
        else:
            return tb


def all_known_jobs(acct_group,uid=None,jobid=None):
    filter=constructFilter(acct_group,uid,jobid)
    queued=ui_condor_q(filter)
    if len(queued.split('\n'))<1:
        queued=''
    history=ui_condor_history(filter)
    if len(history.split('\n'))<1:
        history=''
    all = queued+history
    return all

def api_condor_q(acctgroup, uid, convert=False):
    """ Uses the Condor Python bindings to get information for scheduled jobs.
        Returns a map of objects with the Cluster Id as the key
    """

    schedd = condor.Schedd()
    results = schedd.query('Owner =?= "%s"' % uid)
    all_jobs = dict()
    for classad in results:
        env = dict([x.split('=') for x in classad['Env'].split(';')])
        if env.get('EXPERIMENT') == acctgroup:
            key = classad['ClusterId']
            if convert is True:
                classad = classad_to_dict(classad)
            all_jobs[key] = classad
    return all_jobs

def classad_to_dict(classad):
    """ Converts a ClassAd object to a dictionary. 
    Used for serialization to JSON.
    """
    job_dict = dict()
    for k, v in classad.items():
        job_dict[repr(k)] = repr(v)
    return job_dict

def schedd_list():
    schedds, cmd_err = subprocessSupport.iexe_cmd("""condor_status -schedd -format '%s ' Name """)
    return schedds.split()
    
def schedd_name(arglist=None):
    #logger.log(arglist)
    _list=schedd_list()
    if len(_list) == 1:
        return _list[0]
    _name = "%s" % socket.gethostname()
    if arglist and len(arglist) > 0:
        i = 0
        for arg in arglist:
            arg = str(arg)
            #logger.log("arg %s i %s"%(arg,i))
            if arg == '--schedd':
                _schedd = str(arglist[i + 1])
                if _schedd in _list:
                    return _schedd

            if arg.find('--schedd=') == 0:
                argparts = arg.split('=')
                _schedd =  '='.join(argparts[1:])
                if _schedd in _list:
                    return _schedd
            i = i + 1
    return _name
