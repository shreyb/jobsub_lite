import cherrypy
import os
import getpass
import traceback
from distutils import spawn

from accounting_group import AccountingGroupsResource
from queued_jobs import QueuedJobsResource
from users_jobs import UsersJobsResource
from version import VersionResource
from scheddload import ScheddLoadResource
from util import mkdir_p
from subprocessSupport import iexe_priv_cmd
import jobsub


class ApplicationInitializationError(Exception):
    def __init__(self, err):
        self.err = err
    def __str__(self):
        return "JobSub server initialization failed: %s" % (self.err)


class Root(object):
    pass


root = Root()
root.acctgroups = AccountingGroupsResource()
root.jobs = QueuedJobsResource()
root.users = UsersJobsResource()
root.version = VersionResource()
root.scheddload = ScheddLoadResource()

def create_statedir(log):
    """
    Create Application statedir(s) 
    /var/lib/jobsub             : rexbatch : 755
    /var/lib/jobsub/tmp         : rexbatch : 700
    """

    jobsubConfig = jobsub.JobsubConfig()
    state_dir = jobsubConfig.stateDir
    err = ''
    path = '%s:%s:%s' % (os.environ['PATH'], '.', '/opt/jobsub/server/webapp')
    exe = spawn.find_executable('jobsub_priv', path=path)

    for dir in jobsubConfig.stateDirLayout():
        if not os.path.isdir(dir[0]):
            try:
                cmd = '%s mkdirsAsUser %s %s %s %s' % (
                          exe,
                          os.path.dirname(dir[0]),
                          os.path.basename(dir[0]),
                          getpass.getuser(),
                          dir[1])
                out, err = iexe_priv_cmd(cmd)
                log.error('Created statedir/subdirectories' % dir[0])
            except:
                err = 'Failed creating internal state directory %s' % state_dir
                log.error(err)
                log.error(traceback.format_exc())
                raise ApplicationInitializationError(err)


def initialize(log):
    create_statedir(log)


def application(environ, start_response):
    os.environ['JOBSUB_INI_FILE'] = environ['JOBSUB_INI_FILE']
    os.environ['JOBSUB_ENV_RUNNER'] = environ['JOBSUB_ENV_RUNNER']
    os.environ['JOBSUB_UPS_LOCATION'] = environ['JOBSUB_UPS_LOCATION']
    os.environ['JOBSUB_CREDENTIALS_DIR'] = \
            os.path.expanduser(environ['JOBSUB_CREDENTIALS_DIR'])
    os.environ['KCA_DN_PATTERN_LIST'] = environ['KCA_DN_PATTERN_LIST']
    os.environ['KADMIN_PASSWD_FILE'] = \
            os.path.expanduser(environ['KADMIN_PASSWD_FILE'])
    os.environ['JOBSUB_SERVER_VERSION'] = "__VERSION__.__RELEASE__"
    os.environ['JOBSUB_SERVER_X509_CERT'] = environ['JOBSUB_SERVER_X509_CERT']
    os.environ['JOBSUB_SERVER_X509_KEY'] = environ['JOBSUB_SERVER_X509_KEY']
    script_name = ''
    appname = environ.get('JOBSUB_APP_NAME')
    if appname is not None:
        script_name = os.path.join('/', appname)
        version = environ.get('JOBSUB_VERSION')
        if version is not None:
            script_name = os.path.join(script_name, appname)
    app = cherrypy.tree.mount(root, script_name=script_name, config=None)

    log_dir = environ['JOBSUB_LOG_DIR']
    mkdir_p(log_dir)
    access_log = os.path.join(log_dir, 'access.log')
    error_log = os.path.join(log_dir, 'debug.log')

    cherrypy.config.update({
        'environment': 'embedded',
        'log.screen': False,
        'log.error_file': error_log,
        'log.access_file': access_log
    })

    app.log.error('jobsub_api.py: starting api: JOBSUB_INI_FILE: %s' % \
            os.environ.get('JOBSUB_INI_FILE'))

    initialize(app.log)

    return cherrypy.tree(environ, start_response)

if __name__ == '__main__':
    cherrypy.quickstart(root, '/jobsub')
