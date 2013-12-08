import base64
import threading
import os
import re
import platform
import zipfile

import cherrypy

import logger

if platform.system() == 'Linux':
    import htcondor as condor
    import classad

from datetime import datetime
from shutil import copyfileobj

from cherrypy.lib.static import serve_file

from util import get_uid, mkdir_p
from auth import check_auth
from jobsub import is_supported_accountinggroup, execute_jobsub_command, get_command_path_root
from format import format_response


@cherrypy.popargs('job_id')
class JobsResource(object):

    def doGET(self, job_id):
        schedd = condor.Schedd()
        results = schedd.query()
        if job_id is not None:
            job_id = int(job_id)
            for job in results:
                # TODO: filter by jobs running for the user
                if job['ClusterId'] == job_id:
                    job_dict = dict()
                    for k, v in job.items():
                        job_dict[repr(k)] = repr(v)
                    rc = {'out': job_dict}
                    break
            else:
                err = 'Job with id %s not found in condor queue' % job_id
                logger.log(err)
                rc = {'err': err}
        else:
            # TODO: filter by jobs running for the user
            jobs = list()
            for job in results:
                jobs.append(job['ClusterId'])
            rc = {'out': jobs}

        return rc

    @cherrypy.expose
    @format_response
    def index(self, job_id=None, **kwargs):
        try:
            if cherrypy.request.method == 'GET':
                rc = self.doGET(job_id)
            else:
                err = 'Unsupported method: %s' % cherrypy.request.method
                logger.log(err)
                rc = {'err': err}
        except:
            err = 'Exception on JobsResouce.index'
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc


def zipdir(path, zip):
    for root, dirs, files in os.walk(path):
        for file in files:
            zip.write(os.path.join(root, file))


class SandboxResource(object):

    def doGET(self, acctgroup, job_id, kwargs):
        subject_dn = cherrypy.request.headers.get('Auth-User')
        uid = get_uid(subject_dn)
        command_path_root = get_command_path_root()
        job_log = os.path.join(command_path_root, 'job.log')
        with open(job_log, 'r') as job_log_file:
            job_records = job_log_file.readlines()
            for job_record in job_records:
                rec_job_id, rec_uid, rec_acctgroup, rec_workdir = job_record.split(' ')
                if job_id == rec_job_id[:-1] and acctgroup == rec_acctgroup and uid == rec_uid:
                    # found the path, zip data and return
                    command_path = '%s/%s/%s/%s' % (command_path_root, acctgroup, uid, rec_workdir)
                    zip = zipfile.ZipFile('%s.zip' % rec_workdir, 'w')
                    zipdir(command_path, zip)
                    zip.close()
                    return serve_file(zip.filename, "application/x-download", "attachment")
            else:
                # return error for no data found
                err = 'No sandbox data found for user: %s, acctgroup: %s, job_id %s' % (uid, acctgroup, job_id)
                logger.log(err)
                rc = {'err': err}

        return rc

    @cherrypy.expose
    @format_response
    @check_auth
    def index(self, acctgroup, job_id, **kwargs):
        try:
            if is_supported_accountinggroup(acctgroup):
                if cherrypy.request.method == 'GET':
                    rc = self.doGET(acctgroup, job_id, kwargs)
                else:
                    err = 'Unsupported method: %s' % cherrypy.request.method
                    logger.log(err)
                    rc = {'err': err}
            else:
                # return error for unsupported acctgroup
                err = 'AccountingGroup %s is not configured in jobsub' % acctgroup
                logger.log(err)
                rc = {'err': err}
        except:
            err = 'Exception on AccountJobsResouce.index'
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc


@cherrypy.popargs('job_id')
class AccountJobsResource(object):

    def __init__(self):
        self.sandbox = SandboxResource()

    def doPOST(self, acctgroup, job_id, kwargs):
        if job_id is None:
            logger.log('kwargs: %s' % str(kwargs))
            jobsub_args = kwargs.get('jobsub_args_base64')
            if jobsub_args is not None:
                jobsub_args = base64.b64decode(jobsub_args).rstrip()
                logger.log('jobsub_args: %s' % jobsub_args)
                jobsub_command = kwargs.get('jobsub_command')
                logger.log('jobsub_command: %s' % jobsub_command)
                subject_dn = cherrypy.request.headers.get('Auth-User')
                uid = get_uid(subject_dn)
                workdir_id = '.'
                if jobsub_command is not None:
                    command_path_root = get_command_path_root()
                    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S") # add request id
                    thread_id = threading.current_thread().ident
                    workdir_id = '%s_%s'%(ts, thread_id)
                    command_path = '%s/%s/%s/%s' % (command_path_root, acctgroup, uid, workdir_id)
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
                jobsub_args.insert(0, workdir_id)
                jobsub_args.insert(0, acctgroup)
                jobsub_args.insert(0, uid)

                rc = execute_jobsub_command(jobsub_args)
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

    @cherrypy.expose
    @format_response
    @check_auth
    def index(self, acctgroup, job_id=None, **kwargs):
        try:
            if is_supported_accountinggroup(acctgroup):
                if cherrypy.request.method == 'POST':
                    rc = self.doPOST(acctgroup, job_id, kwargs)
                else:
                    err = 'Unsupported method: %s' % cherrypy.request.method
                    logger.log(err)
                    rc = {'err': err}
            else:
                # return error for unsupported acctgroup
                err = 'AccountingGroup %s is not configured in jobsub' % acctgroup
                logger.log(err)
                rc = {'err': err}
        except:
            err = 'Exception on AccountJobsResouce.index'
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc


