import logger
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



if platform.system() == 'Linux':
    try:
        import htcondor as condor
        import classad
    except:
        logger.log('Cannot import htcondor. Have the condor python bindings been installed?')

def ui_condor_userprio():
        all_users, cmd_err = subprocessSupport.iexe_cmd('condor_userprio -allusers')
        return all_users

def constructFilter( acctgroup=None, uid=None, jobid=None):
    lorw = ' -wide '
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
        host=x[l-1]
        if clusterid.find('.')<0:
	    clusterid=clusterid+'.0'
	job_cnst = """regexp("%s#%s.*",GlobalJobId)""" %(host,clusterid)
    else:
        lorw = ' -long '
        job_cnst = 'ClusterID==%d'%(math.trunc(float(jobid)))
    filter = " %s -constraint '%s && %s && %s' "%(lorw, ac_cnst,usr_cnst,job_cnst)
    return filter

def ui_condor_history(filter=None):
    if filter is None:
        cmd = 'condor_history  -wide'
    else:
        cmd = 'condor_history %s' % filter
    all_jobs, cmd_err = subprocessSupport.iexe_cmd(cmd)
    return all_jobs

def ui_condor_q(filter=None):
    if filter is None:
        cmd = 'condor_q -global -wide'
    else:
        cmd = 'condor_q -g -wide %s' % filter

    all_jobs, cmd_err = subprocessSupport.iexe_cmd(cmd)
    return all_jobs

def all_known_jobs(acct_group,uid=None,jobid=None):
    filter=None
    parts=[]
    if acct_group!='all':
        if uid is None:
            parts.append('stringlistMember("group_%s",AccountingGroup,".")'% acct_group)
        else:
            parts.append('(AccountingGroup==group_%s.%s)' %(acct_group,uid))
    if jobid is not None:
        parts.append('(clusterid==%s)'%jobid)
    if len(parts)>0:
        filter=' -constraint '
        for part in parts:
            filter=filter + part
        filter = filter + "'"
        logger.log("filter=%s"%filter)
    queued=ui_condor_q(filter)
    if len(queued.split('\n'))<=1:
	queued=''
    history=ui_condor_history(filter)
    if len(history.split('\n'))<=1:
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
        """ Converts a ClassAd object to a dictionary. Used for serialization to JSON.
        """
        job_dict = dict()
        for k, v in classad.items():
            job_dict[repr(k)] = repr(v)
        return job_dict

def schedd_name():
	""" returns the name of the local schedd
	"""
	cmd="""condor_status -schedd -format '%s' name -constraint 'regexp("<%s",MyAddress)'""" % ('%s',socket.gethostbyname(socket.gethostname()))
	schedd, cmd_err = subprocessSupport.iexe_cmd(cmd)
	return schedd
