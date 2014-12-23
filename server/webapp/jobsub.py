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
        logger.log("supported groups:%s accountinggroup:%s"%(groups,accountinggroup))
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


def should_transfer_krb5cc(acctgroup):
    can_transfer=False
    p = JobsubConfigParser()
    if p.has_section(acctgroup):
        if p.has_option(acctgroup, 'transfer_krbcc_to_job'):
            can_transfer = p.get(acctgroup, 'transfer_krbcc_to_job')
            if can_transfer=='False':
                can_transfer=False
    if can_transfer:
        logger.log("group %s is authorized to transfer krb5 cache"%acctgroup)
    else:
        logger.log("group %s is NOT authorized to transfer krb5 cache"%acctgroup)

    return can_transfer

"""
# Moved this to auth.py where itbelongs
def get_voms(acctgroup):
    rc = 'fermilab:/fermilab/%s' % acctgroup
    p = JobsubConfigParser()
    if p.has_section(acctgroup):
        if p.has_option(acctgroup, 'voms'):
            rc = p.get(acctgroup, 'voms')
    else:
        raise AcctGroupNotConfiguredError(acctgroup)

    return rc
"""


def get_dropbox_path_root():
    rc = '/opt/jobsub/dropbox'
    p = JobsubConfigParser()
    submit_host = socket.gethostname()
    if p.has_section(submit_host):
        if p.has_option(submit_host, 'dropbox_path_root'):
            rc = p.get(submit_host, 'dropbox_path_root')

    return rc


def execute_jobsub_command(acctgroup, uid, jobsub_args, workdir_id=None,role=None,jobsub_client_version=None):
    #jobsub_args.insert(0, schedd_name())
    #jobsub_args.insert(0, role)
    #jobsub_args.insert(0, workdir_id)
    #jobsub_args.insert(0, acctgroup)
    #jobsub_args.insert(0, uid)

    envrunner = os.environ.get('JOBSUB_ENV_RUNNER', '/opt/jobsub/server/webapp/jobsub_env_runner.sh')
    command = [envrunner] + jobsub_args
    logger.log('jobsub command: %s' % command)
    child_env = os.environ.copy()
    schedd=schedd_name(jobsub_args)
    logger.log('schedd=%s'%schedd)
    child_env['SCHEDD']=schedd
    child_env['ROLE']=str(role)
    child_env['WORKDIR_ID']=str(workdir_id)
    child_env['GROUP']=str(acctgroup)
    child_env['USER']=str(uid)
    child_env['JOBSUB_CLIENT_VERSION']=str(jobsub_client_version)
    if should_transfer_krb5cc(acctgroup):
        creds_base_dir = os.environ.get('JOBSUB_CREDENTIALS_DIR')
        cache_fname = os.path.join(creds_base_dir, 'krb5cc_%s'%uid)
        #logger.log("%s add %s here to transfer_encrypt_files"%(acctgroup,cache_fname))
        child_env['ENCRYPT_INPUT_FILES']=cache_fname
        child_env['KRB5CCNAME']=cache_fname

    
    pp = Popen(command, stdout=PIPE, stderr=PIPE, env=child_env)


    result = {
        'out': pp.stdout.readlines(),
        'err': pp.stderr.readlines()
    }
    for rslt in result['out']:
        if rslt.lower().find('jobsubjobid')>=0:
            logger.log(rslt)
            break
    if len(result['err'])>0:
        logger.log(str(result['err']))
    return result

def execute_dag_command(acctgroup, uid, jobsub_args, workdir_id=None,role=None,jobsub_client_version=None):

    envrunner = os.environ.get('DAGMAN_ENV_RUNNER', '/opt/jobsub/server/webapp/jobsub_dag_runner.sh')
    command = [envrunner] + jobsub_args
    logger.log('jobsub command: %s' % command)
    child_env = os.environ.copy()
    child_env['SCHEDD']=schedd_name()
    child_env['ROLE']=str(role)
    child_env['WORKDIR_ID']=str(workdir_id)
    child_env['GROUP']=str(acctgroup)
    child_env['USER']=str(uid)
    child_env['JOBSUB_CLIENT_VERSION']=str(jobsub_client_version)
    if should_transfer_krb5cc(acctgroup):
        creds_base_dir = os.environ.get('JOBSUB_CREDENTIALS_DIR')
        cache_fname = os.path.join(creds_base_dir, 'krb5cc_%s'%uid)
        child_env['ENCRYPT_INPUT_FILES']=cache_fname
        child_env['KRB5CCNAME']=cache_fname

    
    pp = Popen(command, stdout=PIPE, stderr=PIPE, env=child_env)


    result = {
        'out': pp.stdout.readlines(),
        'err': pp.stderr.readlines()
    }

    for rslt in result['out']:
        if rslt.lower().find('jobsubjobid')>=0:
            logger.log(rslt)
            break
    if len(result['err'])>0:
        logger.log(str(result['err']))
    return result
