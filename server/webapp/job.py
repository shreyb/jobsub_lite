import cherrypy
import base64
import threading
import os
import re
import logger

import platform
if platform.system() == 'Linux':
        import htcondor as condor
        import classad

from datetime import datetime
from subprocess import Popen, PIPE
from shutil import copyfileobj

from util import get_uid, mkdir_p
from auth import check_auth
from jobsub import is_supported_accountinggroup
from format import format_response

@cherrypy.popargs('job_id')
class JobsResource(object):

    def execute_jobsub_command(self, jobsub_args):
        #TODO: the path to the jobsub tool should be configurable
        command = ['/opt/jobsub/server/webapp/jobsub_env_runner.sh'] + jobsub_args
        logger.log('jobsub command: %s' % command)
        pp = Popen(command, stdout=PIPE, stderr=PIPE)
        result = {
            'out': pp.stdout.readlines(),
            'err': pp.stderr.readlines()
        }
        logger.log('jobsub command result: %s' % str(result))
        return result

    def doPOST(self, subject_dn, accountinggroup, job_id, kwargs):
        rc = dict()
        if job_id is None:
            logger.log('kwargs: %s' % str(kwargs))
            jobsub_args = kwargs.get('jobsub_args_base64')
            if jobsub_args is not None:
                jobsub_args = base64.b64decode(jobsub_args).rstrip()
                logger.log('jobsub_args: %s' % jobsub_args)
                jobsub_command = kwargs.get('jobsub_command')
                logger.log('jobsub_command: %s' % jobsub_command)
                if jobsub_command is not None:
                    # TODO: get the command path root from the configuration
                    command_path_root = '/opt/jobsub/uploads'
                    uid = get_uid(subject_dn)
                    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S") # add request id
                    thread_id = threading.current_thread().ident
                    command_path = '%s/%s/%s/%s_%s' % (command_path_root, accountinggroup, uid, ts, thread_id)
                    mkdir_p(command_path)
                    command_file_path = os.path.join(command_path, jobsub_command.filename)
                    logger.log('command_file_path: %s' % command_file_path)
                    with open(command_file_path, 'wb') as dst_file:
                        copyfileobj(jobsub_command.file, dst_file)
                    # replace the command file name in the arguments with the path on the local machine
                    command_tag = '@(.*)%s' % jobsub_command.filename
                    jobsub_args = re.sub(command_tag, command_file_path, jobsub_args)
                    logger.log('jobsub_args (subbed): %s' % jobsub_args)

                jobsub_args = jobsub_args.split(' ')
                rc = self.execute_jobsub_command(jobsub_args)
            else:
                # return an error because no command was supplied
                err = 'User must supply jobsub command'
                logger.log(err)
                rc = {'err': err}
        else:
            # return an error because job_id has been supplied but POST is for creating new jobs
            err = 'User has supplied job_id but POST is for creating new jobs'
            logger.log(err)
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
                    rc = {'out': dict(job)}
                    break
            else:
                err = 'Job with id %s not found in condor queue' % job_id
                logger.log(err)
                rc = {'err': err}
        else:
            # return an error because job_id has not been supplied but GET is for querying jobs
            err = 'User has not supplied job_id but GET is for querying jobs'
            logger.log(err)
            rc = {'err': err}

        return rc

    @cherrypy.expose
    # @format_response
    # @check_auth
    def index(self, accountinggroup, job_id=None, **kwargs):
        content_type_accept = cherrypy.request.headers.get('Accept')
        logger.log('Request content_type_accept: %s' % content_type_accept)
        rc = dict()
        try:
            subject_dn = cherrypy.request.headers.get('Auth-User')
            if subject_dn is not None:
                logger.log('subject_dn: %s, accountinggroup: %s' % (subject_dn, accountinggroup))
                if check_auth(subject_dn, accountinggroup):
                    if accountinggroup is not None:
                        logger.log('subject_dn: %s, accountinggroup: %s' % (subject_dn, accountinggroup))
                        if is_supported_accountinggroup(accountinggroup):
                            if cherrypy.request.method == 'POST':
                                rc = self.doPOST(subject_dn, accountinggroup, job_id, kwargs)
                            elif cherrypy.request.method == 'GET':
                                rc = self.doGET(subject_dn, accountinggroup, job_id, kwargs)
                        else:
                            # return error for unsupported accountinggroup
                            err = 'AccountingGroup %s is not configured in jobsub' % accountinggroup
                            logger.log(err)
                            rc = {'err': err}
                    else:
                        # return error for no accountinggroup
                        err = 'User has not supplied accountinggroup'
                        logger.log(err)
                        rc = {'err': err}
                else:
                    # return error for failed auth
                    err = 'User authorization has failed'
                    logger.log(err)
                    rc = {'err': err}
            else:
                # return error for no subject_dn
                err = 'User has not supplied subject dn'
                logger.log(err)
                rc = {'err': err}
        except:
            err = 'Exception on JobsResouce.index'
            logger.log(err, traceback=True)
            rc = {'err': err}

        return format_response(content_type_accept, rc)


