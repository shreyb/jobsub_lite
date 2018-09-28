"""file: jobsub.py
    Description:
        utility functions

    Project:
        JobSub

    Author:
        Parag Mhashilkar
"""

import os
import logging
import cherrypy
import pwd
import pipes
import socket
from distutils import spawn
import StringIO

import subprocessSupport
import condor_commands
from JobsubConfigParser import JobsubConfigParser
from request_headers import get_client_dn

if os.getenv('JOBSUB_USE_FAKE_LOGGER'):
    import FakeLogger as logger
else:
    import logger


def is_supported_accountinggroup(acctgroup):
    """Is acctgroup configured in jobsub.ini?
    """
    r_code = False
    try:
        prs = JobsubConfigParser()
        groups = prs.supportedGroups()
        logger.log("supported groups:%s accountinggroup:%s" %
                   (groups, acctgroup))
        r_code = (acctgroup in groups)
    except Exception:
        logger.log('Failed to get accounting groups: ',
                   traceback=True, severity=logging.ERROR)
        logger.log('Failed to get accounting groups: ',
                   traceback=True,
                   severity=logging.ERROR,
                   logfile='error')

    return r_code


def global_superusers():
    """return a list of global_superusers
       global_superusers can hold,release,remove other
       users jobs and browse
       other users sandboxes regardless of other
       settings
    """

    g_list = []
    prs = JobsubConfigParser()
    global_susers = prs.get('default', 'global_superusers')
    if global_susers:
        for itm in global_susers.split():
            g_list.append(itm)
    logger.log('returning %s' % g_list)
    return g_list


def group_superusers(acctgroup):
    """return a list of superusers for acctgroup
       group_superusers can hold,release,remove other
       users jobs in that acctgroup and can browse
       other users sandboxes in that group regardless of other
       settings
    """

    g_list = []
    prs = JobsubConfigParser()
    susers = prs.get(acctgroup, 'group_superusers')
    if susers:
        for itm in susers.split():
            g_list.append(itm)
    logger.log('returning %s' % g_list)
    return g_list


def is_superuser_for_group(acctgroup, user):
    """is user 'user' a superuser in acctgroup 'acctgroup'?
    """
    logger.log('checking if %s in %s is group_superuser' % (user, acctgroup))
    if is_supported_accountinggroup(acctgroup):
        su_list = group_superusers(acctgroup)
        logger.log('sulist is %s for %s' % (su_list, acctgroup))
        return user in su_list
    raise Exception('group %s not supported' % acctgroup)


def is_global_superuser(user):
    gsu = global_superusers()
    return user in gsu


def sandbox_readable_by_group(acctgroup):
    """return True if anyone in acctgroup can read and fetch
       others sandboxes.  Configured in jobsub.ini
    """
    r_code = False
    try:
        prs = JobsubConfigParser()
        r_code = prs.get(acctgroup, 'sandbox_readable_by_group')
        logger.log('sandbox_readable_by_group:%s is %s' % (acctgroup, r_code))
        return r_code
    except Exception:
        logger.log('Failed to get sandbox_readable_by_group: ',
                   traceback=True,
                   severity=logging.ERROR)
        logger.log('Failed to get sandbox_readable_by_group: ',
                   traceback=True,
                   severity=logging.ERROR,
                   logfile='error')

    return r_code


def sandbox_allowed_browsable_file_types():
    """file extensions that are readable via the web browser
       set in jobsub.ini
    """
    r_code = []
    try:
        prs = JobsubConfigParser()
        extensions = prs.get(prs.submit_host,
                             'output_files_web_browsable_allowed_types')
        if isinstance(extensions, str):
            r_code = extensions.split()
        logger.log('output_files_web_browsable_allowed_types %s' % (r_code))
        return r_code
    except Exception:
        logger.log('Failed to get output_files_web_browsable_allowed_types: ',
                   traceback=True,
                   severity=logging.ERROR)
        logger.log('Failed to get output_files_web_browsable_allowed_types: ',
                   traceback=True,
                   severity=logging.ERROR,
                   logfile='error')

    return r_code


def get_supported_accountinggroups():
    """return a list of all supported accounting groups
       in jobsub.ini
    """
    r_code = list()
    try:
        prs = JobsubConfigParser()
        r_code = prs.supportedGroups()
    except Exception:
        logger.log('Failed to get accounting groups: ',
                   traceback=True,
                   severity=logging.ERROR)
        logger.log('Failed to get accounting groups: ',
                   traceback=True,
                   severity=logging.ERROR,
                   logfile='error')

    return r_code


def default_voms_role(acctgroup="default"):
    """Return the default VOMS role for acctgroup
       its usually 'Analysis' but can be set to something
       else in jobsub.ini
    """

    r_code = None
    try:
        prs = JobsubConfigParser()
        r_code = prs.get(acctgroup, 'default_voms_role')
        logger.log('default voms role for %s : %s' % (acctgroup, r_code))
    except Exception:
        logger.log('error fetching voms role for acctgroup :%s' % acctgroup,
                   severity=logging.ERROR,
                   traceback=True)
        logger.log('error fetching voms role for acctgroup :%s' % acctgroup,
                   severity=logging.ERROR,
                   traceback=True,
                   logfile='error')
    return r_code


def sub_group_pattern(acctgroup):
    """strings to feed to voms-proxy-init for subgroups
       see mars subgroups in jobsub.ini
    """
    prs = JobsubConfigParser()
    acg = acctgroup
    try:
        sgp = prs.get(acctgroup, 'sub_group_pattern')
        if sgp:
            acg = sgp
    except Exception:
        pass
    return acg


def get_dropbox_max_size(acctgroup):
    """Scan jobsub.ini for dropbox on pnfs areas that acctgroup
       uses, return a string
    """
    r_code_default = '1073741824'
    logger.log(
        "default = %s attempting to find dropbox_max_size" %
        r_code_default)
    try:
        prs = JobsubConfigParser()
        r_code = prs.get(acctgroup, 'dropbox_max_size')
        logger.log("r_code = %s" % r_code)
    except Exception:
        logger.log('Failed to get dropbox_max_size: ',
                   traceback=True,
                   severity=logging.ERROR)
    if r_code:
        return r_code
    else:
        return r_code_default


def get_dropbox_constraint(acctgroup):
    """Scan jobsub.ini for dropbox condor_q query constraint
       uses, return a string
    """
    try:
        prs = JobsubConfigParser()
        r_code = prs.get(acctgroup, 'dropbox_constraint')
        logger.log("r_code = %s" % r_code)
        cnstr = r_code % acctgroup
        logger.log("returning = %s" % cnstr)
        return cnstr
    except Exception:
        logger.log('Failed to get dropbox_constraint: ',
                   traceback=True,
                   severity=logging.ERROR)
        cnstr = '(jobsub_group=?="%s")&&(PNFS_INPUT_FILES=!=Null)' % acctgroup
        logger.log("returning = %s" % cnstr)
        return cnstr


def get_dropbox_location(acctgroup):
    """Scan jobsub.ini for dropbox on pnfs areas that acctgroup
       uses, return a string
    """
    r_code = None
    try:
        prs = JobsubConfigParser()
        r_code = prs.get(acctgroup, 'dropbox_location')
        try:
            # First, check to see if dropbox is turned "off" in jobsub.ini.
            r_code = prs.getboolean(acctgroup, 'dropbox_location')
        except ValueError:
            try:
                r_code_sub = r_code % acctgroup
                r_code = r_code_sub
            except TypeError:
                # Substitution failed, so return original r_code
                pass
    except Exception:
        logger.log('Failed to get dropbox_location: ',
                   traceback=True,
                   severity=logging.ERROR)
        logger.log('Failed to get dropbox_location: ',
                   traceback=True,
                   severity=logging.ERROR,
                   logfile='error')
    return r_code


def get_dropbox_upload_list(acctgroup):
    """Return all files uploaded to jobsub using dropbox:// and tardir:// URIs,
    using jobsub.ini to verify that these are jobsub-managed areas
    """
    dropbox_upload_set = set()    # Use set to ensure uniqueness automatically
    dropbox_location = get_dropbox_location(acctgroup)
    if not dropbox_location:
        return False

    a_filter = "-constraint '%s' " % get_dropbox_constraint(acctgroup)
    a_key = ['PNFS_INPUT_FILES']

    dropbox_uploads = condor_commands.ui_condor_q(a_filter=a_filter,
                                                  a_key=a_key)

    query_rslt = dropbox_uploads.split('\n')

    # This should automatically take care of the no-jobs or error case
    for line in query_rslt:
        for item in line.split(','):
            if dropbox_location in item:
                dropbox_upload_set.add(item)

    return list(dropbox_upload_set)


def get_authentication_methods(acctgroup):
    """Scan jobsub.ini for authentication methods that acctgroup
       uses, return as a list
    """
    try:
        prs = JobsubConfigParser()
        r_code = prs.get(acctgroup, 'authentication_methods')
    except Exception:
        logger.log('Failed to get authentication_methods: ',
                   traceback=True,
                   severity=logging.ERROR)
        logger.log('Failed to get authentication_methods: ',
                   traceback=True,
                   severity=logging.ERROR,
                   logfile='error')

    methods = list()
    for meth in r_code.split(','):
        methods.append(meth.strip())
    return methods


def get_submit_reject_threshold():
    """return submit_reject_threshold
       from jobsub.ini
    """
    sdf = 0.85
    prs = JobsubConfigParser()
    if prs.has_section('default'):
        if prs.has_option('default', 'submit_reject_threshold'):
            sdf = prs.get('default', 'submit_reject_threshold')
    logger.log('submit_reject_threshold=%s' % sdf)
    return float(sdf)


def get_command_path_root():
    """return root directory of sandboxes
       from jobsub.ini
    """
    cpr = '/opt/jobsub/uploads'
    prs = JobsubConfigParser()
    submit_host = socket.gethostname()
    if prs.has_section(submit_host):
        if prs.has_option(submit_host, 'command_path_root'):
            cpr = prs.get(submit_host, 'command_path_root')

    return cpr


def should_transfer_krb5cc(acctgroup):
    """some acctgroups such as CDF and D0 still
       need to transfer a kerberos ticket to the
       worker node for file transfer.  Check if this
       is in jobsub.ini
    """
    can_transfer = False
    prs = JobsubConfigParser()
    if prs.has_section(acctgroup):
        if prs.has_option(acctgroup, 'transfer_krbcc_to_job'):
            can_transfer = prs.get(acctgroup, 'transfer_krbcc_to_job')
            if can_transfer == 'False':
                can_transfer = False
    if can_transfer:
        logger.log("group %s is authorized to transfer krb5 cache" % acctgroup)
    else:
        logger.log(
            "group %s is NOT authorized to transfer krb5 cache" % acctgroup)

    return can_transfer


def get_dropbox_path_root():
    """return root of dropbox path
       from jobsub.ini
    """
    dpr = '/opt/jobsub/dropbox'
    prs = JobsubConfigParser()
    submit_host = socket.gethostname()
    if prs.has_section(submit_host):
        if prs.has_option(submit_host, 'dropbox_path_root'):
            dpr = prs.get(submit_host, 'dropbox_path_root')

    return dpr


def get_jobsub_wrapper(submit_type='job'):
    """find shell correct script wrapper
       depending on
       @submit_type = 'job' or 'dag'
    """
    exepath = '/opt/jobsub/server/webapp'
    wrapper = os.environ.get('JOBSUB_ENV_RUNNER',
                             os.path.join(exepath,
                                          'jobsub_env_runner.sh'))
    if submit_type == 'dag':
        wrapper = os.environ.get('DAGMAN_ENV_RUNNER',
                                 os.path.join(exepath,
                                              'jobsub_dag_runner.sh'))
    return wrapper


def log_msg(acctgroup, username, jobsub_args, role=None,
            submit_type='job', jobsub_client_version='UNKNOWN',
            jobsub_client_krb5_principal='UNKNOWN'):
    """create a 'submitted command X , jobsubjobid=Y' message
       to be logged
    """
    if jobsub_client_version in ['UNKNOWN', '__VERSION__']:
        jobsub_client_version = '?'
    if jobsub_client_krb5_principal == 'UNKNOWN':
        jobsub_client_krb5_principal = '?'
    log_str = "%s %s %s %s" % \
        (cherrypy.request.headers.get('Remote-Addr'),
         jobsub_client_krb5_principal,
         username,
         jobsub_client_version)
    cmd = " jobsub_submit "
    if submit_type == 'dag':
        cmd = " jobsub_submit_dag "
    role_c = ''
    if role and role != default_voms_role(acctgroup):
        role_c = " --role %s " % role
    short_args = []
    for arg in jobsub_args:
        if '--export_env=' not in arg:
            short_args.append(os.path.basename(arg))
    log_str = "%s %s --group %s %s %s " % (log_str,
                                           cmd,
                                           acctgroup,
                                           role_c,
                                           ' '.join(short_args))
    return log_str


def execute_job_submit_wrapper(acctgroup, username, jobsub_args,
                               workdir_id=None, role=None,
                               jobsub_client_version='UNKNOWN',
                               jobsub_client_krb5_principal='UNKNOWN',
                               submit_type='job', priv_mode=True,
                               child_env=None):
    """submit a job or dag
    """
    envrunner = get_jobsub_wrapper(submit_type=submit_type)
    command = [envrunner] + jobsub_args
    logger.log('jobsub command: %s' % command)
    out = err = ''
    if not child_env:
        child_env = os.environ.copy()
    child_env['JOBSUB_CLIENT_VERSION'] = jobsub_client_version
    child_env['JOBSUB_CLIENT_KRB5_PRINCIPAL'] = jobsub_client_krb5_principal
    child_env['GROUP'] = acctgroup

    if priv_mode:
        jobsubConfig = JobsubConfig()
        # Only required for the job submission
        job_submit_dir = os.path.join(
            jobsubConfig.commandPathUser(acctgroup, username),
            workdir_id)

        schedd_nm = condor_commands.schedd_name(jobsub_args)
        recent_duty_cycle = float(
            condor_commands.schedd_recent_duty_cycle(schedd_nm))
        srt = get_submit_reject_threshold()

        if recent_duty_cycle > srt:
            err = "schedd %s is overloaded " % schedd_nm
            err += "at %s percent busy " % (100.0 * recent_duty_cycle)
            err += "rejecting job submission, try again in a few minutes"
            result = {'err': err}
            logger.log(err)
            cherrypy.response.status = 500
            return result

        child_env['JOBSUB_INTERNAL_ACTION'] = 'SUBMIT'
        child_env['SCHEDD'] = schedd_nm
        if role:
            child_env['ROLE'] = role
        child_env['WORKDIR_ID'] = workdir_id
        child_env['USER'] = username
        child_env['COMMAND_PATH_ROOT'] = jobsubConfig.commandPathRoot
        child_env['JOBSUB_CLIENT_DN'] = get_client_dn()
        rm_ip = cherrypy.request.headers.get('Remote-Addr')
        child_env['JOBSUB_CLIENT_IP_ADDRESS'] = rm_ip

        if '--sendtkt' in jobsub_args and should_transfer_krb5cc(acctgroup):
            src_cache_fname = os.path.join(jobsubConfig.krb5cc_dir,
                                           'krb5cc_%s' % username)
            dst_cache_fname = os.path.join(
                job_submit_dir, 'krb5cc_%s' % username)

            copy_file_as_user(src_cache_fname, dst_cache_fname, username)
            logger.log('Added %s for acctgroup %s to transfer_encrypt_files' %
                       (dst_cache_fname, acctgroup))
            child_env['ENCRYPT_INPUT_FILES'] = dst_cache_fname
            child_env['KRB5CCNAME'] = dst_cache_fname

        out, err = run_cmd_as_user(command, username, child_env=child_env)
    else:
        # Some commands like --help do: not need sudo
        out, err = subprocessSupport.iexe_cmd('%s' % ' '.join(command),
                                              child_env=child_env)

    sub_msg = log_msg(acctgroup, username, jobsub_args, role,
                      submit_type, jobsub_client_version,
                      jobsub_client_krb5_principal)

    # Convert the output to list as in case of previous version of jobsub
    if (isinstance(out, type('string'))) and out.strip():
        out = StringIO.StringIO('%s\n' % out.rstrip('\n')).readlines()
    if (isinstance(err, type('string'))) and err.strip():
        err = StringIO.StringIO('%s\n' % err.rstrip('\n')).readlines()
    for line in out:
        if 'jobsubjobid' in line.lower():
            sub_msg += line
            logger.log(sub_msg, logfile='submit')
            logger.log(sub_msg)
    if len(err):
        for line in err:
            sub_msg += line
        logger.log(sub_msg, severity=logging.ERROR, logfile='submit')
        logger.log(sub_msg, severity=logging.ERROR, logfile='error')
        logger.log(sub_msg, severity=logging.ERROR)
    result = {
        'out': out,
        'err': err
    }

    return result


class JobsubConfig(object):
    """Class representing and creating expected directory structure on
       jobsub server
    """

    def __init__(self):
        """constructor
        """

        self.state_dir = os.environ.get('JOBSUB_STATE_DIR', '/var/lib/jobsub')

        self.tmp_dir = os.path.join(self.state_dir, 'tmp')
        self.creds_dir = os.path.join(self.state_dir, 'creds')

        self.keytabs_dir = os.path.join(self.creds_dir, 'keytabs')
        self.certs_dir = os.path.join(self.creds_dir, 'certs')
        self.proxies_dir = os.path.join(self.creds_dir, 'proxies')
        self.krb5cc_dir = os.path.join(self.creds_dir, 'krb5cc')

        self.commandPathRoot = get_command_path_root()

    def state_dir_layout(self):
        layout = [
            (self.state_dir, '0755'),
            (self.creds_dir, '0755'),
            (self.keytabs_dir, '0755'),
            (self.certs_dir, '0755'),
            (self.proxies_dir, '0755'),
            (self.krb5cc_dir, '0755'),
            (self.tmp_dir, '1777'),
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
            if os.stat(user_dir).st_uid != pwd.getpwnam(username).pw_uid:
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
    """return priv_mode tool to create and move files and directories
       as a given user
    """
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
    except Exception as e:
        err_str = 'Error creating dir as user using command '
        err_str += '%s:\nSTDOUT:%s\nSTDERR:%s\nException:%s'
        raise RuntimeError(err_str % (cmd, out, err, e))
        #raise RuntimeError, err_str % (cmd, out, err, e)


def move_file_as_user(src, dst, username):
    exe = get_jobsub_priv_exe()
    cmd = '%s moveFileAsUser "%s" "%s" "%s"' % (exe, src, dst, username)
    out = err = ''
    logger.log(cmd)
    try:
        out, err = subprocessSupport.iexe_priv_cmd(cmd)
    except Exception as e:
        err_str = 'Error moving file as user using command '
        err_str += '%s:\nSTDOUT:%s\nSTDERR:%s\nException:%s'
        raise RuntimeError(err_str % (cmd, out, err, e))


def copy_file_as_user(src, dst, username):
    exe = get_jobsub_priv_exe()
    cmd = '%s copyFileAsUser "%s" "%s" "%s"' % (exe, src, dst, username)
    out = err = ''
    logger.log(cmd)
    try:
        out, err = subprocessSupport.iexe_priv_cmd(cmd)
    except Exception as e:
        err_str = 'Error copying file as user using command '
        err_str += '%s:\nSTDOUT:%s\nSTDERR:%s\nException:%s'
        raise RuntimeError(err_str % (cmd, out, err, e))


def chown_as_user(path, username):
    exe = get_jobsub_priv_exe()
    cmd = '%s chown "%s" "%s"' % (exe, path, username)
    out = err = ''
    logger.log(cmd)
    try:
        out, err = subprocessSupport.iexe_priv_cmd(cmd)
    except Exception as e:
        err_str = 'Error changing ownership of path as user using '
        err_str += 'command %s:\nSTDOUT:%s\nSTDERR:%s\nException:%s'
        raise RuntimeError(err_str % (cmd, out, err, e))


def run_cmd_as_user(command, username, child_env={}):
    exe = get_jobsub_priv_exe()
    c = ' '.join(pipes.quote(s) for s in command)
    cmd = '%s runCommand %s' % (exe, c)
    out = err = ''
    logger.log(cmd)
    try:
        out, err = subprocessSupport.iexe_priv_cmd(cmd, child_env=child_env,
                                                   username=username)
    except Exception as e:
        err_fmt = 'Error running as user %s using command '
        err_fmt += '%s:\nSTDOUT:%s\nSTDERR:%s\nException:%s'
        err_str = err_fmt % (username, cmd, out, err, e)
        logger.log(err_str, severity=logging.ERROR)
        logger.log(err_str, severity=logging.ERROR, logfile='condor_commands')
        logger.log(err_str, severity=logging.ERROR, logfile='error')
        err = err_str

    return out, err


def condor_bin(cmd):
    """
    Return the full path to the HTCondor command 'cmd'
    """

    exe = spawn.find_executable(cmd)
    if not exe:
        raise Exception("Unable to find command '%s' in the PATH." % exe)
    return exe


if __name__ == '__main__':
    # export PYTHONPATH=jobsub/server/webapp
    # export PYTHONPATH=$PYTHONPATH:jobsub/lib/logger
    # export PYTHONPATH=$PYTHONPATH:jobsub/lib/JobsubConfigParser
    # export JOBSUB_INI_FILE=/opt/jobsub/server/conf.jobsub.ini
    # export JOBSUB_USE_FAKE_LOGGER=true
    # possibly export JOBSUB_SUPPRESS_LOG_OUTPUT=true
    print 'put some test code here'
