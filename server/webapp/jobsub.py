from subprocess import Popen, PIPE
from condor_commands import schedd_name
import logger
import os
import socket


from JobsubConfigParser import JobsubConfigParser

class AcctGroupNotConfiguredError(Exception):
    def __init__(self, acctgroup):
        self.acctgroup = acctgroup
        Exception.__init__(self, "AcctGroup='%s' not configured on this server" % (self.acctgroup))


def is_supported_accountinggroup(accountinggroup):
    rc = False
    try:
        p = JobsubConfigParser()
        groups = p.supportedGroups()
        rc = (accountinggroup in groups)
    except:
        logger.log('Failed to get accounting groups: ', traceback=True)

    return rc


def get_supported_accountinggroups():
    rc = list()
    try:
        p = JobsubConfigParser()
        rc = p.supportedGroups()
    except:
        logger.log('Failed to get accounting groups: ', traceback=True)

    return rc


def get_command_path_root():
    rc = '/opt/jobsub/uploads'
    p = JobsubConfigParser()
    submit_host = socket.gethostname()
    if p.has_section(submit_host):
        if p.has_option(submit_host, 'command_path_root'):
            rc = p.get(submit_host, 'command_path_root')

    return rc


def get_voms(acctgroup):
    rc = 'fermilab:/fermilab/%s' % acctgroup
    p = JobsubConfigParser()
    if p.has_section(acctgroup):
        if p.has_option(acctgroup, 'voms'):
            rc = p.get(acctgroup, 'voms')
    else:
        raise AcctGroupNotConfiguredError(acctgroup)

    return rc


def get_dropbox_path_root():
    rc = '/opt/jobsub/dropbox'
    p = JobsubConfigParser()
    submit_host = socket.gethostname()
    if p.has_section(submit_host):
        if p.has_option(submit_host, 'dropbox_path_root'):
            rc = p.get(submit_host, 'dropbox_path_root')

    return rc


def execute_jobsub_command(acctgroup, uid, jobsub_args, workdir_id='None',role='None'):
    jobsub_args.insert(0, schedd_name())
    jobsub_args.insert(0, role)
    jobsub_args.insert(0, workdir_id)
    jobsub_args.insert(0, acctgroup)
    jobsub_args.insert(0, uid)

    envrunner = os.environ.get('JOBSUB_ENV_RUNNER', '/opt/jobsub/server/webapp/jobsub_env_runner.sh')
    command = [envrunner] + jobsub_args
    logger.log('jobsub command: %s' % command)
    pp = Popen(command, stdout=PIPE, stderr=PIPE)
    result = {
        'out': pp.stdout.readlines(),
        'err': pp.stderr.readlines()
    }
    errlist=result['err']
    newlist=[]
    ignore_msg='jobsub.ini for jobsub config'
    for m in errlist:
        if ignore_msg not in m:
            newlist.append(m)
    result['err']=newlist
    logger.log('jobsub command result: %s' % str(result))

    return result
