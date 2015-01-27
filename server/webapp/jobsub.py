from subprocess import Popen, PIPE
from condor_commands import schedd_name
import logger
import os
import socket
from distutils import spawn
import subprocessSupport


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



def get_jobsub_wrapper(submit_type='job'):

    wrapper = os.environ.get('JOBSUB_ENV_RUNNER',
                             '/opt/jobsub/server/webapp/jobsub_env_runner.sh')
    if submit_type == 'dag':
        wrapper = os.environ.get('DAGMAN_ENV_RUNNER',
                                 '/opt/jobsub/server/webapp/jobsub_dag_runner.sh')
    return wrapper


def check_command_path_user(acctgroup_dir, username):
    """
    Check if user specific jobs dir exists and is owned by the user.
    If not create it or change the ownership accordingly.
    """


    if os.path.exists(os.path.join(acctgroup_dir, username)):
        # Check and change ownership as required
        pass
    else:
        create_dir_as_user(acctgroup_dir, username, username, mode='755')


def execute_job_submit_wrapper(acctgroup, username, jobsub_args,
                               workdir_id=None, role=None,
                               jobsub_client_version=None,
                               submit_type='job'):

    envrunner = get_jobsub_wrapper(submit_type=submit_type)
    command = [envrunner] + jobsub_args
    logger.log('jobsub command: %s' % command)
    child_env = os.environ.copy()
    child_env['SCHEDD'] = schedd_name()
    child_env['ROLE'] = role
    child_env['WORKDIR_ID'] = workdir_id
    child_env['GROUP'] = acctgroup
    child_env['USER'] = username
    child_env['JOBSUB_CLIENT_VERSION'] = jobsub_client_version
    if should_transfer_krb5cc(acctgroup):
        cache_fname = os.path.join(get_jobsub_creds_dir(), 'krb5cc_%s'%uid)
        logger.log('Adding %s for acctgroup %s to transfer_encrypt_files'%(cache_fname, acctgroup))
        child_env['ENCRYPT_INPUT_FILES']=cache_fname
        child_env['KRB5CCNAME']=cache_fname


    pp = Popen(command, stdout=PIPE, stderr=PIPE, env=child_env)

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


def execute_jobsub_command(acctgroup, uid, jobsub_args, workdir_id=None,role=None,jobsub_client_version=None):

    envrunner = os.environ.get('JOBSUB_ENV_RUNNER', '/opt/jobsub/server/webapp/jobsub_env_runner.sh')
    command = [envrunner] + jobsub_args
    logger.log('jobsub command: %s' % command)
    logger.log('----- user: %s' % uid)
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


############
# TODO: Following should be converted to config class and members
############

def get_jobsub_state_dir():
    return os.environ.get('JOBSUB_STATE_DIR', '/var/lib/jobsub')


def get_jobsub_creds_dir():
    return os.path.join(get_jobsub_state_dir(), 'creds')


def get_jobsub_keytabs_dir():
    return os.path.join(get_jobsub_creds_dir(), 'keytabs')


def get_jobsub_certs_dir():
    return os.path.join(get_jobsub_creds_dir(), 'certs')


def get_jobsub_proxies_dir():
    return os.path.join(get_jobsub_creds_dir(), 'proxies')


def get_jobsub_krb5cc_dir():
    return os.path.join(get_jobsub_creds_dir(), 'krb5cc')


def get_jobsub_tmp_dir():
    return os.path.join(get_jobsub_state_dir(), 'tmp')


def get_jobsub_statedir_hierarchy():
    hierarchy = [
        (get_jobsub_state_dir(), '0755'),
        (get_jobsub_creds_dir(), '0755'),
        (get_jobsub_keytabs_dir(), '0755'),
        (get_jobsub_certs_dir(), '0755'),
        (get_jobsub_proxies_dir(), '0755'),
        (get_jobsub_krb5cc_dir(), '0755'),
        (os.path.join(get_jobsub_state_dir(), 'tmp'), '1777'),
    ]
    return hierarchy


def get_command_path_acctgroup(acctgroup):
    return os.path.join(get_command_path_root(), acctgroup)


def get_command_path_user(acctgroup, user):
    return os.path.join(get_command_path_acctgroup(acctgroup), user)


############
# TODO: Following should be converted to class and helper functions
############
def get_jobsub_priv_exe():
    # TODO: Need to find a proper library for this call
    path = '%s:%s:%s' % (os.environ['PATH'], '.', '/opt/jobsub/server/webapp')
    exe = spawn.find_executable('jobsub_priv', path=path)
    if not exe:
        raise Exception("Unable to find command '%s' in the PATH." % exe)
    return exe


def create_dir_as_user(base_dir, sub_dirs, username, mode='700'):
    exe = get_jobsub_priv_exe()
    out = err = ''
    # Create the dir as user
    cmd = '%s mkdirsAsUser "%s" "%s" "%s" "%s"' % (exe, base_dir, sub_dirs,
                                                   username, mode)
    logger.log(cmd)
    try:
        out, err = subprocessSupport.iexe_priv_cmd(cmd)
    except Exception, e:
        err_str = 'Error creating dir as user using command %s:\nSTDOUT:%s\nSTDERR:%s\nException:%s' 
        raise RuntimeError, err_str % (cmd, out, err, e)
        #raise RuntimeError, err_str % (cmd, out, err, e)



def move_file_as_user(src, dst, username):
    exe = get_jobsub_priv_exe()
    cmd = '%s moveFileAsUser "%s" "%s" "%s"' % (exe, src, dst, username)
    out = err = ''
    logger.log(cmd)
    try:
        out, err = subprocessSupport.iexe_priv_cmd(cmd)
    except Exception, e:
        err_str = 'Error moving file as user using command %s:\nSTDOUT:%s\nSTDERR:%s\nException:%s'
        raise RuntimeError, err_str % (cmd, out, err, e)
