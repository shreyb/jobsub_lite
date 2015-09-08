import base64
import random
import os
import re
import cherrypy
import logger
import sys
import StringIO
import util

from datetime import datetime
from shutil import copyfileobj

from tempfile import NamedTemporaryFile
from auth import check_auth, x509_proxy_fname
from jobsub import is_supported_accountinggroup
from jobsub import execute_job_submit_wrapper
from jobsub import JobsubConfig
from jobsub import create_dir_as_user
from jobsub import move_file_as_user
from jobsub import condor_bin
from jobsub import run_cmd_as_user
from format import format_response
from condor_commands import condor
from condor_commands import constructFilter, ui_condor_q, schedd_list
from sandbox import SandboxResource
from history import HistoryResource
from dag import DagResource
from queued_long import QueuedLongResource
from queued_dag import QueuedDagResource
from by_user import AccountJobsByUserResource
from forcex_jobid import RemoveForcexByJobIDResource



@cherrypy.popargs('job_id')
class AccountJobsResource(object):
    def __init__(self):
        cherrypy.request.role = None
        cherrypy.request.username = None
        cherrypy.request.vomsProxy = None
        self.sandbox = SandboxResource()
        self.history = HistoryResource()
        self.dag = DagResource()
        self.long = QueuedLongResource()
        self.dags = QueuedDagResource()
        self.user = AccountJobsByUserResource()
        self.forcex = RemoveForcexByJobIDResource()


    def doGET(self, acctgroup, job_id, kwargs):
        """ Serves the following APIs:

            Query a single job. Returns a JSON map of the ClassAd 
            object that matches the job id
            API is /jobsub/acctgroups/<group_id>/jobs/<job_id>/

            Query list of jobs. Returns a JSON map of all the ClassAd 
            objects in the queue
            API is /jobsub/acctgroups/<group_id>/jobs/
        """
        uid = kwargs.get('user_id')
        filter = constructFilter(acctgroup,uid,job_id)
        logger.log('filter=%s'%filter)
        q=ui_condor_q(filter)
        all_jobs=q.split('\n')
        if len(all_jobs)<1:
            logger.log('condor_q %s returned no jobs'%filter)
            err = 'Job with id %s not found in condor queue' % job_id
            rc={'err':err}
        else:
            rc={'out':all_jobs}

        return rc




    def doPOST(self, acctgroup, job_id, kwargs):
        """ Create/Submit a new job. Returns the output from the jobsub tools.
            API is /jobsub/acctgroups/<group_id>/jobs/<job_id>/
        """

        if job_id is None:
            child_env = os.environ.copy()
            jobsubConfig = JobsubConfig()
            logger.log('job.py:doPost:kwargs: %s' % kwargs)
            jobsub_args = kwargs.get('jobsub_args_base64')
            jobsub_client_version = kwargs.get('jobsub_client_version')
            jobsub_client_krb5_principal = kwargs.get('jobsub_client_krb5_principal','UNKNOWN')
            if jobsub_args is not None:

                jobsub_args = base64.urlsafe_b64decode(str(jobsub_args)).rstrip()
                logger.log('jobsub_args: %s' % jobsub_args)
                jobsub_command = kwargs.get('jobsub_command')
                role  = kwargs.get('role')
                logger.log('job.py:doPost:jobsub_command %s' %(jobsub_command))
                logger.log('job.py:doPost:role %s ' % (role))

                command_path_acctgroup = jobsubConfig.commandPathAcctgroup(acctgroup)
                util.mkdir_p(command_path_acctgroup)
                command_path_user = jobsubConfig.commandPathUser(acctgroup,
                                                                 cherrypy.request.username)
                # Check if the user specific dir exist with correct
                # ownership. If not create it.
                jobsubConfig.initCommandPathUser(acctgroup, cherrypy.request.username)

                ts = datetime.now().strftime("%Y-%m-%d_%H%M%S.%f")
                uniquer=random.randrange(0,10000)
                workdir_id = '%s_%s' % (ts, uniquer)
                command_path = os.path.join(command_path_acctgroup, 
                                            cherrypy.request.username, workdir_id)
                logger.log('command_path: %s' % command_path)
                child_env['X509_USER_PROXY'] = x509_proxy_fname(cherrypy.request.username,
                                                                 acctgroup, role)
                # Create the job's working directory as user 
                create_dir_as_user(command_path_user, workdir_id,
                                   cherrypy.request.username, mode='755')
                if jobsub_command is not None:
                    command_file_path = os.path.join(command_path,
                                                     jobsub_command.filename)
                    child_env['JOBSUB_COMMAND_FILE_PATH']=command_file_path
                    cf_path_w_space = ' %s'%command_file_path
                    logger.log('command_file_path: %s' % command_file_path)
                    # First create a tmp file before moving the command file
                    # in place as correct user under the jobdir
                    tmp_file_prefix = os.path.join(jobsubConfig.tmpDir,
                                                   jobsub_command.filename)
                    tmp_cmd_fd = NamedTemporaryFile(prefix="%s_"%tmp_file_prefix,
                                                    delete=False)
                    copyfileobj(jobsub_command.file, tmp_cmd_fd)

                    tmp_cmd_fd.close()
                    move_file_as_user(tmp_cmd_fd.name, command_file_path, cherrypy.request.username)
                    #with open(command_file_path, 'wb') as dst_file:
                    #    copyfileobj(jobsub_command.file, dst_file)

                    # replace the command file name in the arguments with 
                    # the path on the local machine.  
                    jobsub_args = re.sub('^@',' @',jobsub_args)
                    command_tag = '\ \@(\S*)%s' % jobsub_command.filename
                    jobsub_args = re.sub(command_tag, cf_path_w_space, jobsub_args)
                    logger.log('jobsub_args (subbed): %s' % jobsub_args)

                jobsub_args = jobsub_args.split(' ')
                rc = execute_job_submit_wrapper(
                         acctgroup=acctgroup, username=cherrypy.request.username,
                         jobsub_args=jobsub_args, workdir_id=workdir_id,
                         role=role, jobsub_client_version=jobsub_client_version,
                         jobsub_client_krb5_principal=jobsub_client_krb5_principal,
                         child_env=child_env)
                if rc.get('out'):
                    for line in rc['out']:
                        if 'jobsubjobid' in line.lower():
                            logger.log(line)
                if rc.get('err'):
                    logger.log(rc['err'])
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
    @check_auth(pass_through='GET')

    def index(self, acctgroup, job_id=None,  **kwargs):
        try:
            logger.log('job_id=%s '%(job_id))
            logger.log('kwargs=%s '%(kwargs))
            if not job_id:
                job_id=kwargs.get('job_id')
            cherrypy.request.role = kwargs.get('role')
            cherrypy.request.username = kwargs.get('username')
            cherrypy.request.vomsProxy = kwargs.get('voms_proxy')
            if is_supported_accountinggroup(acctgroup):
                if cherrypy.request.method == 'POST':
                    #create job
                    rc = self.doPOST(acctgroup, job_id, kwargs)
                elif cherrypy.request.method == 'GET':
                    #query job
                    rc = self.doGET(acctgroup, job_id, kwargs)
                elif cherrypy.request.method == 'DELETE':
                    #remove job
                    rc = util.doDELETE(acctgroup, job_id=job_id, **kwargs)
                elif cherrypy.request.method == 'PUT':
                    #hold/release
                    rc = util.doPUT(acctgroup, job_id=job_id,  **kwargs)
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
            cherrypy.response.status = 500
            err = 'Exception on AccountJobsResource.index'
            logger.log(err, traceback=True)
            rc = {'err': err}
        if rc.get('err'):
            cherrypy.response.status = 500
        return rc


