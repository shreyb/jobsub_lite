import cherrypy
import json
import base64
import os
import re
import errno
import threading

try:
    import htcondor as condor
    import classad
except:
    import traceback
    traceback.print_exc()

from subprocess import Popen, PIPE
from shutil import copyfileobj
from datetime import datetime
from pprint import pformat


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def format_response(content_type, data):
    content_type_list = content_type.split(',')
    if 'application/json' in content_type_list:
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return str(json.dumps(data))
    elif 'text/plain' in content_type_list:
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return str(pformat(data))
    elif 'text/html' in content_type_list:
        cherrypy.response.headers['Content-Type'] = 'text/html'
        return str(pformat(data))
    else:
        return 'Content type %s not supported' % content_type


@cherrypy.popargs('accountinggroup')
class AccountingGroupsResource(object):
    def __init__(self):
        self.jobs = JobsResource()

@cherrypy.popargs('job_id')
class JobsResource(object):

    def execute_jobsub_command(self, jobsub_args):
        #TODO: the path to the jobsub tool should be configurable
        command = ['/opt/jobsub/jobsub_env_runner.sh'] + jobsub_args
        cherrypy.request.app.log.error('jobsub command: %s' % command)
        pp = Popen(command, stdout=PIPE, stderr=PIPE)
        result = {
            'out': pp.stdout.readlines(),
            'err': pp.stderr.readlines()
        }
        cherrypy.request.app.log.error('jobsub command result: %s' % str(result))
        return result

    def execute_gums_command(self, subject_dn, accountinggroup):
        command = '/usr/bin/gums-host|mapUser|-g|https://gums.fnal.gov:8443/gums/services/GUMSXACMLAuthorizationServicePort|%s|-f|/fermilab/%s' % (subject_dn, accountinggroup)
        command = command.split('|')
        cherrypy.request.app.log.error('gums command: %s' % command)
        pp = Popen(command, stdout=PIPE, stderr=PIPE)
        result = {
            'out': pp.stdout.readlines(),
            'err': pp.stderr.readlines()
        }
        cherrypy.request.app.log.error('gums command result: %s' % str(result))
        return result

    def gums_auth(self, subject_dn, accountinggroup):
        result = self.execute_gums_command(subject_dn, accountinggroup)
        if result['out'][0].startswith('null') or len(result['err']) > 0:
            return False
        else:
            return True

    def is_supported_accountinggroup(self, accountinggroup):
        # TODO: get list of accountinggroups from jobsub config
        return True

    def get_uid(self, subject_dn):
        uid = 'unknown'
        try:
            uid = subject_dn.split(':')[1]
        except:
            cherrypy.request.app.log.error('Exception getting uid', traceback=True)
        return uid

    def doPOST(self, subject_dn, accountinggroup, job_id, kwargs):
        rc = dict()
        if job_id is None:
            cherrypy.request.app.log.error('kwargs: %s' % str(kwargs))
            jobsub_args = kwargs.get('jobsub_args_base64')
            if jobsub_args is not None:
                jobsub_args = base64.b64decode(jobsub_args).rstrip()
                cherrypy.request.app.log.error('jobsub_args: %s' % jobsub_args)
                jobsub_command = kwargs.get('jobsub_command')
                cherrypy.request.app.log.error('jobsub_command: %s' % jobsub_command)
                if jobsub_command is not None:
                    # TODO: get the command path root from the configuration
                    command_path_root = '/opt/jobsub/uploads'
                    uid = self.get_uid(subject_dn)
                    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S") # add request id
                    thread_id = threading.current_thread().ident
                    command_path = '%s/%s/%s/%s_%s' % (command_path_root, accountinggroup, uid, ts, thread_id)
                    mkdir_p(command_path)
                    command_file_path = os.path.join(command_path, jobsub_command.filename)
                    cherrypy.request.app.log.error('command_file_path: %s' % command_file_path)
                    with open(command_file_path, 'wb') as dst_file:
                        copyfileobj(jobsub_command.file, dst_file)
                    # replace the command file name in the arguments with the path on the local machine
                    command_tag = '@(.*)%s' % jobsub_command.filename
                    jobsub_args = re.sub(command_tag, command_file_path, jobsub_args)
                    cherrypy.request.app.log.error('jobsub_args (subbed): %s' % jobsub_args)

                jobsub_args = jobsub_args.split(' ')
                rc = self.execute_jobsub_command(jobsub_args)
            else:
                # return an error because no command was supplied
                err = 'User must supply jobsub command'
                cherrypy.request.app.log.error(err)
                rc = {'err': err}
        else:
            # return an error because job_id has been supplied but POST is for creating new jobs
            err = 'User has supplied job_id but POST is for creating new jobs'
            cherrypy.request.app.log.error(err)
            rc = {'err': err}

        return rc

    def doGET(self, subject_dn, accountinggroup, job_id, kwargs):
        rc = dict()
        if job_id is not None:
            job_id = int(job_id)
            schedd = condor.Schedd()
            results = schedd.query()
            for job in results:
                if job['ClusterId'] == job_id:
                    rc = {'out': repr(job)}
            else:
                err = 'Job with id %s not found in condor queue' % job_id
                cherrypy.request.app.log.error(err)
                rc = {'err': err}
        else:
            # return an error because job_id has not been supplied but GET is for querying jobs
            err = 'User has not supplied job_id but GET is for querying jobs'
            cherrypy.request.app.log.error(err)
            rc = {'err': err}

        return rc

    @cherrypy.expose
    def index(self, accountinggroup, job_id=None, **kwargs):
        content_type_accept = cherrypy.request.headers.get('Accept')
        cherrypy.request.app.log.error('Request content_type_accept: %s' % content_type_accept)
        rc = dict()
        try:
            subject_dn = cherrypy.request.headers.get('Auth-User')
            if subject_dn is not None and accountinggroup is not None:
                cherrypy.request.app.log.error('subject_dn: %s, accountinggroup: %s' % (subject_dn, accountinggroup))
                if self.is_supported_accountinggroup(accountinggroup):
                    if self.gums_auth(subject_dn, accountinggroup):
                        if cherrypy.request.method == 'POST':
                            rc = self.doPOST(subject_dn, accountinggroup, job_id, kwargs)
                        elif cherrypy.request.method == 'GET':
                            rc = self.doGET(subject_dn, accountinggroup, job_id, kwargs)
                    else:
                        # return error for failed gums auth
                        err = 'User authorization has failed'
                        cherrypy.request.app.log.error(err)
                        rc = {'err': err}
                else:
                    # return error for unsupported accountinggroup
                    err = 'AccountingGroup %s is not configured in jobsub' % accountinggroup
                    cherrypy.request.app.log.error(err)
                    rc = {'err': err}
            else:
                # return error for no subject_dn and accountinggroup
                err = 'User has not supplied subject dn and accountinggroup'
                cherrypy.request.app.log.error(err)
                rc = {'err': err}
        except:
            err = 'Exception on JobsResouce.index'
            cherrypy.request.app.log.error(err, traceback=True)
            rc = {'err': err}

        return format_response(content_type_accept, rc)


class Root(object):
    pass

root = Root()

root.accountinggroups = AccountingGroupsResource()

if __name__ == '__main__':
    cherrypy.quickstart(root, '/jobsub')
else:
    cherrypy.config.update({
        'environment': 'embedded',
        'lob.screen': False,
        'log.error_file': '/opt/jobsub/jobsub_error.log',
        'log.access_file': '/opt/jobsub/jobsub_access.log'
    })
    application = cherrypy.Application(root, script_name=None, config=None)


"""
import cherrypy

from accountinggroups import AccountingGroups


class Root(object):
    pass

root = Root()

root.accountinggroups = AccountingGroups()

# TODO: conf should be in seperate module for difference between dev and prod
conf = {
    'global': {
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 8080,
    },
    '/': {
        'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
    }
}

#TODO: server start will be different for dev and prod. Prod will be WSGI
cherrypy.quickstart(root, '/jobsub', conf)
"""
