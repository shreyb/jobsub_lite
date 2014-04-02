import base64
#import threading
import random
import os
import re
import platform
import cherrypy
import logger
import math

from util import encode_multipart_formdata

if platform.system() == 'Linux':
    try:
        import htcondor as condor
        import classad
    except:
        logger.log('Cannot import htcondor. Have the condor python bindings been installed?')

from datetime import datetime
from shutil import copyfileobj

from cherrypy.lib.static import serve_file

from util import get_uid, mkdir_p, create_zipfile
from auth import check_auth, get_x509_proxy_file
from jobsub import is_supported_accountinggroup, execute_jobsub_command, get_command_path_root
from format import format_response


condor_job_status = {
    1: 'Idle',
    2: 'Running',
    3: 'Removed',
    4: 'Completed',
    5: 'Held',
    6: 'Transferring Output',
}


def get_condor_queue(acctgroup, uid, convert=False):
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


def cleanup(zip_file, outfilename):
    """ Hook function to cleanup sandbox files after request has been processed
    """
             
    try:
        os.remove(outfilename)
    except:
        err = 'Failed to remove encoded file at %s' % outfilename
        logger.log(err)
    try:
        os.remove(zip_file)
    except:
        err = 'Failed to remove zip file at %s' % zip_file
        logger.log(err)


class SandboxResource(object):
    """ Download compressed output sandbox for a given job
        API is /jobsub/acctgroups/<group_id>/jobs/<job_id>/sandbox/
    """


    def doGET(self, acctgroup, job_id, kwargs):
        subject_dn = cherrypy.request.headers.get('Auth-User')
        uid = get_uid(subject_dn)
        command_path_root = get_command_path_root()
        if job_id is not None:
            job_status = None
            all_jobs = get_condor_queue(acctgroup, uid)
            classad = all_jobs.get(math.trunc(float(job_id)))
            if classad is not None:
                job_status = condor_job_status.get(classad.get('JobStatus'))
            job_tokens = job_id.split('.')
            if len(job_tokens) == 1 or (len(job_tokens) > 1 and job_tokens[-1].isdigit() is False):
                job_id = '%s.0' % job_id
            zip_path = os.path.join(command_path_root, acctgroup, uid, job_id)
            if os.path.exists(zip_path):
                # found the path, zip data and return
                if job_status is None:
                    job_status = 'Completed'
                zip_file = os.path.join(command_path_root, acctgroup, uid, '%s.zip' % job_id)
                create_zipfile(zip_file, zip_path, job_id)

                rc = {'job_status': job_status}

                with open(zip_file, 'rb') as fh:
                    fields = [('rc', rc)]
                    files = [('zip_file', zip_file, fh.read())]
                    outfilename = os.path.join(command_path_root, acctgroup, uid, '%s.encoded' % job_id)
                    with open(outfilename, 'wb') as outfile:
                        content_type = encode_multipart_formdata(fields, files, outfile)
                    cherrypy.request.hooks.attach('on_end_request', cleanup, zip_file=zip_file, outfilename=outfilename)
                    return serve_file(outfilename, 'application/x-download')

            else:
                # return error for no data found
                err = 'No sandbox data found for user: %s, acctgroup: %s, job_id %s' % (uid, acctgroup, job_id)
                logger.log(err)
                rc = {'job_status': job_status, 'err': err}
                cherrypy.response.status = 404
        else:
            jobs_file_path = os.path.join(command_path_root, acctgroup, uid)
            sandbox_cluster_ids = list()
            if os.path.exists(jobs_file_path):
                root, dirs, files = os.walk(jobs_file_path, followlinks=False)
                for dir in dirs:
                    if os.path.islink(os.path.join(jobs_file_path, dir)):
                        sandbox_cluster_ids.append(dir)
                rc = {'out': sandbox_cluster_ids}
            else:
                # return error for no data found
                err = 'No sandbox data found for user: %s, acctgroup: %s' % (uid, acctgroup)
                logger.log(err)
                rc = {'err': err}
                cherrypy.response.status = 404

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
                    cherrypy.response.status = 500
            else:
                # return error for unsupported acctgroup
                err = 'AccountingGroup %s is not configured in jobsub' % acctgroup
                logger.log(err)
                rc = {'err': err}
                cherrypy.response.status = 500
        except:
            err = 'Exception on AccountJobsResource.index'
            logger.log(err, traceback=True)
            rc = {'err': err}
            cherrypy.response.status = 500
  
        return rc


@cherrypy.popargs('job_id')
class AccountJobsResource(object):
    def __init__(self):
        self.sandbox = SandboxResource()
        self.condorActions = {
            'REMOVE': condor.JobAction.Remove,
            'HOLD': condor.JobAction.Hold,
            'RELEASE': condor.JobAction.Release,
        }


    def doGET(self, acctgroup, job_id):
        """ Serves the following APIs:

            Query a single job. Returns a JSON map of the ClassAd 
            object that matches the job id
            API is /jobsub/acctgroups/<group_id>/jobs/<job_id>/

            Query list of jobs. Returns a JSON map of all the ClassAd 
            objects in the queue
            API is /jobsub/acctgroups/<group_id>/jobs/
        """
        subject_dn = cherrypy.request.headers.get('Auth-User')
        uid = get_uid(subject_dn)
        if job_id is not None:
            all_jobs = get_condor_queue(acctgroup, uid)
            classad = all_jobs.get(int(job_id))
            if classad is not None:
                job_dict = classad_to_dict(classad)
                rc = {'out': job_dict}
            else:
                err = 'Job with id %s not found in condor queue' % job_id
                logger.log(err)
                rc = {'err': err}
        else:
            all_jobs = get_condor_queue(acctgroup, uid, True)
            rc = {'out': all_jobs}

        return rc


    def doDELETE(self, acctgroup, job_id):
        rc = {'out': None, 'err': None}

        if job_id:
            rc['out'] = self.doJobAction(
                            acctgroup, job_id,
                            self.condorActions['REMOVE'])
        else:
            # Error because job_id is required to DELETE jobs
            err = 'No job id specified with DELETE action'
            logger.log(err)
            rc['err'] = err

        return rc


    def doPUT(self, acctgroup, job_id, kwargs):
        rc = {'out': None, 'err': None}

        job_action = kwargs.get('job_action')
        if job_action and job_id:

            if job_action.upper() in self.condorActions:
                rc['out'] = self.doJobAction(
                                acctgroup, job_id,
                                self.condorActions[job_action.upper()])
            else:
                rc['err'] = '%s is not a valid action on jobs' % job_action

        elif not job_id:
            # Error because job_id is required to DELETE jobs
            rc['err'] = 'No job id specified with DELETE action'
        else:
            # Error because no args informing the action hold/release given
            rc['err'] = 'No action (hold/release) specified with PUT action'

        logger.log(rc)

        return rc


    def doPOST(self, acctgroup, job_id, kwargs):
        """ Create/Submit a new job. Returns the output from the jobsub tools.
            API is /jobsub/acctgroups/<group_id>/jobs/<job_id>/
        """

        if job_id is None:
            logger.log('job.py:doPost:kwargs: %s' % kwargs)
            jobsub_args = kwargs.get('jobsub_args_base64')
            if jobsub_args is not None:

                jobsub_args = base64.urlsafe_b64decode(str(jobsub_args)).rstrip()
                logger.log('jobsub_args: %s' % jobsub_args)
                jobsub_command = kwargs.get('jobsub_command')
                role  = kwargs.get('role')
                logger.log('job.py:doPost:jobsub_command %s' %(jobsub_command))
                logger.log('job.py:doPost:role %s ' % (role))
                subject_dn = cherrypy.request.headers.get('Auth-User')
                uid = get_uid(subject_dn)
                command_path_root = get_command_path_root()
                ts = datetime.now().strftime("%Y-%m-%d_%H%M%S.%f") # add request id
                uniquer=random.randrange(0,10000)
                workdir_id = '%s_%s' % (ts, uniquer)
                command_path = os.path.join(command_path_root, acctgroup, uid, workdir_id)
                logger.log('command_path: %s' % command_path)
                mkdir_p(command_path)
                if jobsub_command is not None:
                    command_file_path = os.path.join(command_path, jobsub_command.filename)
                    logger.log('command_file_path: %s' % command_file_path)
                    with open(command_file_path, 'wb') as dst_file:
                        copyfileobj(jobsub_command.file, dst_file)
                    # replace the command file name in the arguments with 
                    # the path on the local machine.  It should be the 
                    # last '@' in the args
                    command_tag = '@(?!.*@)(.*)%s' % jobsub_command.filename
                    jobsub_args = re.sub(command_tag, command_file_path, jobsub_args)
                    logger.log('jobsub_args (subbed): %s' % jobsub_args)

                jobsub_args = jobsub_args.split(' ')

                rc = execute_jobsub_command(acctgroup, uid, jobsub_args, workdir_id, role)
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
                elif cherrypy.request.method == 'GET':
                    rc = self.doGET(acctgroup,job_id)
                elif cherrypy.request.method == 'DELETE':
                    rc = self.doDELETE(acctgroup, job_id)
                elif cherrypy.request.method == 'PUT':
                    rc = self.doPUT(acctgroup, job_id, kwargs)
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
            err = 'Exception on AccountJobsResource.index'
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc



    def doJobAction(self, acctgroup, job_id, job_action):
        dn = cherrypy.request.headers.get('Auth-User')
        uid = get_uid(dn)
        constraint = '(AccountingGroup =?= "group_%s.%s") && (Owner =?= "%s")' % (acctgroup, uid, uid)
        # Split the jobid to get cluster_id and proc_id
        ids = job_id.split('.')
        constraint = '%s && (ClusterId == %s)' % (constraint, ids[0])
        if (len(ids) > 1) and (ids[1]):
            constraint = '%s && (ProcId == %s)' % (constraint, ids[1])

        logger.log('Performing %s on jobs with constraints (%s)' % (job_action, constraint))

        schedd = condor.Schedd()
        out = schedd.act(job_action, constraint)
        logger.log(('%s' % (out)).replace('\n', ' '))

        return "Performed %s on %s jobs matching your request" % (job_action, out['TotalSuccess'])
