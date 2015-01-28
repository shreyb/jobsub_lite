import base64
import random
import os
import re
import cherrypy
import logger
import math
import subprocessSupport 

from datetime import datetime
from shutil import copyfileobj

from cherrypy.lib.static import serve_file
from tempfile import NamedTemporaryFile
from util import get_uid, mkdir_p
from auth import check_auth, x509_proxy_fname
from jobsub import is_supported_accountinggroup
from jobsub import execute_jobsub_command
from jobsub import execute_job_submit_wrapper
from jobsub import get_jobsub_tmp_dir
from jobsub import get_command_path_root
from jobsub import get_command_path_acctgroup
from jobsub import get_command_path_user
from jobsub import check_command_path_user
from jobsub import create_dir_as_user
from jobsub import move_file_as_user
from format import format_response
from condor_commands import condor, api_condor_q,ui_condor_q
from condor_commands import classad_to_dict,constructFilter
from sandbox import SandboxResource
from history import HistoryResource
from dag import DagResource
from queued_long import QueuedLongResource
from queued_dag import QueuedDagResource



@cherrypy.popargs('job_id')
class AccountJobsResource(object):
    def __init__(self):
	self.role = None
	self.username = None
	self.vomsProxy = None
        self.sandbox = SandboxResource()
	self.history = HistoryResource()
        self.dag = DagResource()
	self.long = QueuedLongResource()
	self.dags = QueuedDagResource()
        self.condorActions = {
            'REMOVE': condor.JobAction.Remove,
            'HOLD': condor.JobAction.Hold,
            'RELEASE': condor.JobAction.Release,
        }


    def doGET(self, acctgroup, job_id, kwargs):
        """ Serves the following APIs:

            Query a single job. Returns a JSON map of the ClassAd 
            object that matches the job id
            API is /jobsub/acctgroups/<group_id>/jobs/<job_id>/

            Query list of jobs. Returns a JSON map of all the ClassAd 
            objects in the queue
            API is /jobsub/acctgroups/<group_id>/jobs/
        """
        #subject_dn = cherrypy.request.headers.get('Auth-User')
        #uid = get_uid(subject_dn)
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
            jobsub_client_version = kwargs.get('jobsub_client_version')
            if jobsub_args is not None:

                jobsub_args = base64.urlsafe_b64decode(str(jobsub_args)).rstrip()
                logger.log('jobsub_args: %s' % jobsub_args)
                jobsub_command = kwargs.get('jobsub_command')
                role  = kwargs.get('role')
                logger.log('job.py:doPost:jobsub_command %s' %(jobsub_command))
                logger.log('job.py:doPost:role %s ' % (role))
                #subject_dn = cherrypy.request.headers.get('Auth-User')

                command_path_acctgroup = get_command_path_acctgroup(acctgroup)
                mkdir_p(command_path_acctgroup)
                command_path_user = get_command_path_user(acctgroup,
                                                          self.username)
                # Check if the user specific dir exist with correct
                # ownership. If not create it.
                check_command_path_user(command_path_acctgroup, self.username)

                ts = datetime.now().strftime("%Y-%m-%d_%H%M%S.%f")
                uniquer=random.randrange(0,10000)
                workdir_id = '%s_%s' % (ts, uniquer)
                command_path = os.path.join(command_path_acctgroup, 
                                            self.username, workdir_id)
                logger.log('command_path: %s' % command_path)
		os.environ['X509_USER_PROXY'] = x509_proxy_fname(self.username,
                                                                 acctgroup, role)
                # Create the job's working directory as user 
                create_dir_as_user(command_path_user, workdir_id,
                                   self.username, mode='755')
                if jobsub_command is not None:
                    command_file_path = os.path.join(command_path,
                                                     jobsub_command.filename)
                    os.environ['JOBSUB_COMMAND_FILE_PATH']=command_file_path
                    cf_path_w_space = ' %s'%command_file_path
                    logger.log('command_file_path: %s' % command_file_path)
                    # First create a tmp file before moving the command file
                    # in place as correct user under the jobdir
                    tmp_file_prefix = os.path.join(get_jobsub_tmp_dir(),
                                                   jobsub_command.filename)
                    tmp_cmd_fd = NamedTemporaryFile(prefix="%s_"%tmp_file_prefix,
                                                    delete=False)
                    copyfileobj(jobsub_command.file, tmp_cmd_fd)

                    tmp_cmd_fd.close()
                    move_file_as_user(tmp_cmd_fd.name, command_file_path, self.username)
                    #with open(command_file_path, 'wb') as dst_file:
                    #    copyfileobj(jobsub_command.file, dst_file)

                    # replace the command file name in the arguments with 
                    # the path on the local machine.  
                    command_tag = '\ \@(\S*)%s' % jobsub_command.filename
                    jobsub_args = re.sub(command_tag, cf_path_w_space, jobsub_args)
                    logger.log('jobsub_args (subbed): %s' % jobsub_args)

                jobsub_args = jobsub_args.split(' ')

                rc = execute_job_submit_wrapper(
                         acctgroup=acctgroup, username=self.username,
                         jobsub_args=jobsub_args, workdir_id=workdir_id,
                         role=role, jobsub_client_version=jobsub_client_version)
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
    def default(self,kwargs):
	logger.log('kwargs=%s'%kwargs)
	return {'out':"kwargs=%s"%kwargs}

    @cherrypy.expose
    @format_response
    @check_auth
    def index(self, acctgroup, job_id=None, **kwargs):
        try:
            self.role = kwargs.get('role')
            self.username = kwargs.get('username')
            self.vomsProxy = kwargs.get('voms_proxy')
            if is_supported_accountinggroup(acctgroup):
                if cherrypy.request.method == 'POST':
                    rc = self.doPOST(acctgroup, job_id, kwargs)
                elif cherrypy.request.method == 'GET':
                    rc = self.doGET(acctgroup,job_id, kwargs)
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
            cherrypy.response.status = 500
            err = 'Exception on AccountJobsResource.index'
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc



    def doJobAction(self, acctgroup, job_id, job_action):
        warning=''
        dn = cherrypy.request.headers.get('Auth-User')
        uid = get_uid(dn)
        #constraint = '(AccountingGroup =?= "group_%s.%s") && (Owner =?= "%s")' % (acctgroup, uid, uid)
        constraint = '(Owner =?= "%s")' % (uid)
        # Split the jobid to get cluster_id and proc_id
	stuff=job_id.split('@')
	schedd_name='@'.join(stuff[1:])
	logger.log("schedd_name is %s"%schedd_name)
        ids = stuff[0].split('.')
        constraint = '%s && (ClusterId == %s)' % (constraint, ids[0])
        if (len(ids) > 1) and (ids[1]):
            constraint = '%s && (ProcId == %s)' % (constraint, ids[1])

        logger.log('Performing %s on jobs with constraints (%s)' % (job_action, constraint))
	coll = condor.Collector()
	if schedd_name == '':
		schedd=condor.Schedd()
	else:
		try:
			schedd_addr = coll.locate(condor.DaemonTypes.Schedd, schedd_name)
                        schedd = condor.Schedd(schedd_addr)
		except:
                        warning='Failed to locate schedd %s,  will try with local schedd.  '%schedd_name
                        logger.log(warning)
			schedd=condor.Schedd()

	#os.environ['X509_USER_PROXY']=x509_proxy_fname(uid,acctgroup)
	os.environ['X509_USER_PROXY']=x509_proxy_fname(uid,acctgroup,self.role)
        out = schedd.act(job_action, constraint)
        logger.log(('%s' % (out)).replace('\n', ' '))
        retStr=''
        if len(warning)>0:
            retStr=warning
        retStr=retStr+ "Performed %s on %s jobs matching your request" % (job_action, out['TotalSuccess'])
        return retStr
