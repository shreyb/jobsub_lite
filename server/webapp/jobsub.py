from subprocess import Popen, PIPE
from condor_commands import schedd_name
import logger
import os
import pwd
import pipes
import socket
from distutils import spawn
import subprocessSupport
import StringIO


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


def get_authentication_methods(acctgroup):
    rc = 'kca-dn'
    try:
        p = JobsubConfigParser()
        if p.has_section(acctgroup):
            if p.has_option(acctgroup, 'authentication_methods'):
                rc = p.get(acctgroup, 'authentication_methods')
    except:
        logger.log('Failed to get accounting groups: ', traceback=True)

    methods = list()
    for m in rc.split(','):
        methods.append(m.strip())
    return methods


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


def execute_job_submit_wrapper(acctgroup, username, jobsub_args,
                               workdir_id=None, role=None,
                               jobsub_client_version='UNKNOWN',
                               submit_type='job', priv_mode=True):

    envrunner = get_jobsub_wrapper(submit_type=submit_type)
    command = [envrunner] + jobsub_args
    logger.log('jobsub command: %s' % command)

    out = err = ''
    child_env = os.environ.copy()
    child_env['JOBSUB_CLIENT_VERSION'] = jobsub_client_version
    child_env['GROUP'] = acctgroup

    if priv_mode:
        jobsubConfig = JobsubConfig()
        # Only required for the job submission
        job_submit_dir = os.path.join(
                             jobsubConfig.commandPathUser(acctgroup, username),
                             workdir_id)

        child_env['JOBSUB_INTERNAL_ACTION'] = 'SUBMIT'
        child_env['SCHEDD'] = schedd_name()
        child_env['ROLE'] = role
        child_env['WORKDIR_ID'] = workdir_id
        child_env['USER'] = username
        child_env['COMMAND_PATH_ROOT'] = jobsubConfig.commandPathRoot
        if should_transfer_krb5cc(acctgroup):
            src_cache_fname = os.path.join(jobsubConfig.krb5ccDir,
                                           'krb5cc_%s'%username)
            dst_cache_fname = os.path.join(job_submit_dir, 'krb5cc_%s'%username)

            copy_file_as_user(src_cache_fname, dst_cache_fname, username)
            logger.log('Adding %s for acctgroup %s to transfer_encrypt_files'%(dst_cache_fname, acctgroup))
            child_env['ENCRYPT_INPUT_FILES'] = dst_cache_fname
            child_env['KRB5CCNAME'] = dst_cache_fname

        out, err = run_cmd_as_user(command, username, child_env=child_env)
    else:
        # Some commands like --help do not need sudo
        out, err = subprocessSupport.iexe_cmd('%s' % ' '.join(command),
                                              child_env=child_env)

    # Convert the output to list as in case of previous version of jobsub
    if (type(out) == type('string')) and out.strip():
        out = StringIO.StringIO('%s\n' % out.rstrip('\n')).readlines()
    if (type(err) == type('string')) and err.strip():
        err = StringIO.StringIO('%s\n' % err.rstrip('\n')).readlines()

    result = {
        'out': out,
        'err': err
    }

    return result


class JobsubConfig:

    def __init__(self):
 
        self.stateDir = os.environ.get('JOBSUB_STATE_DIR', '/var/lib/jobsub')

        self.tmpDir = os.path.join(self.stateDir, 'tmp')
        self.credsDir = os.path.join(self.stateDir, 'creds')

        self.keytabsDir = os.path.join(self.credsDir, 'keytabs')
        self.certsDir = os.path.join(self.credsDir, 'certs')
        self.proxiesDir = os.path.join(self.credsDir, 'proxies')
        self.krb5ccDir = os.path.join(self.credsDir, 'krb5cc')

        self.commandPathRoot = get_command_path_root()


    def stateDirLayout(self):
        layout = [
            (self.stateDir, '0755'),
            (self.credsDir, '0755'),
            (self.keytabsDir, '0755'),
            (self.certsDir, '0755'),
            (self.proxiesDir, '0755'),
            (self.krb5ccDir, '0755'),
            (self.tmpDir, '1777'),
        ]
        return layout


    def commandPathAcctgroup(self, acctgroup):
        return os.path.join(self.commandPathRoot, acctgroup)


    def commandPathUser(self, acctgroup, user):
        return os.path.join(self.commandPathAcctgroup(acctgroup), user)


    def initCommandPathUser(self, acctgroup, username):
        """
        Check if user specific jobs dir exists and is owned by the user.
        If not create it or change the ownership accordingly.
        """

        user_dir = self.commandPathUser(acctgroup, username)
        if os.path.exists(user_dir):
            # Check and change ownership as required.
            # Only invoked after the upgrade from legacy code or
            # when there is a change in GUMS mapping
            if (os.stat(user_dir).st_uid != pwd.getpwnam(username).pw_uid):
                chown_as_user(user_dir, username)
        else:
            acctgroup_dir = self.commandPathAcctgroup(acctgroup)
            if not os.path.exists(acctgroup_dir):
                os.makedirs(acctgroup_dir)
            create_dir_as_user(acctgroup_dir, username, username, mode='755')


#jobsubConfig = JobsubConfig()

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


def copy_file_as_user(src, dst, username):
    exe = get_jobsub_priv_exe()
    cmd = '%s copyFileAsUser "%s" "%s" "%s"' % (exe, src, dst, username)
    out = err = ''
    logger.log(cmd)
    try:
        out, err = subprocessSupport.iexe_priv_cmd(cmd)
    except Exception, e:
        err_str = 'Error copying file as user using command %s:\nSTDOUT:%s\nSTDERR:%s\nException:%s'
        raise RuntimeError, err_str % (cmd, out, err, e)


def chown_as_user(path, username):
    exe = get_jobsub_priv_exe()
    cmd = '%s chown "%s" "%s"' % (exe, path, username)
    out = err = ''
    logger.log(cmd)
    try:
        out, err = subprocessSupport.iexe_priv_cmd(cmd)
    except Exception, e:
        err_str = 'Error changing ownership of path as user using command %s:\nSTDOUT:%s\nSTDERR:%s\nException:%s'
        raise RuntimeError, err_str % (cmd, out, err, e)


def run_cmd_as_user(command, username, child_env={}):
    exe = get_jobsub_priv_exe()
    c = ' '.join(pipes.quote(s) for s in command)
    cmd = '%s runCommand %s' % (exe, c)
    out = err = ''
    logger.log(cmd)
    try:
        out, err = subprocessSupport.iexe_priv_cmd(cmd, child_env=child_env,
                                                   username=username)
    except Exception, e:
        err_str = 'Error running as user %s using command %s:\nSTDOUT:%s\nSTDERR:%s\nException:%s'
        raise RuntimeError, err_str % (username, cmd, out, err, e)

    return out, err


def condor_bin(cmd):
    """
    Return the full path to the HTCondor command
    """

    exe = spawn.find_executable(cmd)
    if not exe:
        raise Exception("Unable to find command '%s' in the PATH." % exe)
    return exe
