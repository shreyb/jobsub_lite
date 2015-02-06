import base64
import random
import os
import re
import cherrypy
import logger
import math
import subprocessSupport 
import tarfile

from datetime import datetime
from shutil import copyfileobj

from cherrypy.lib.static import serve_file

from tempfile import NamedTemporaryFile

from util import mkdir_p
from auth import check_auth, x509_proxy_fname
from jobsub import is_supported_accountinggroup
from jobsub import JobsubConfig
from jobsub import get_command_path_root
from jobsub import execute_job_submit_wrapper
from jobsub import JobsubConfig
from jobsub import get_command_path_root
from jobsub import create_dir_as_user
from jobsub import move_file_as_user
from jobsub import run_cmd_as_user

from format import format_response
from sandbox import SandboxResource
from dag_help import DAGHelpResource



@cherrypy.popargs('job_id')
class DagResource(object):
    
    def __init__(self):
       self.help = DAGHelpResource()
       self.username = None
       self.vomsProxy = None
       self.payLoadFileName = 'payload.tgz'


    def doPOST(self, acctgroup, job_id, kwargs):
        """ Create/Submit a new dag. Returns the output from the jobsub tools.
            API is /jobsub/acctgroups/<group_id>/jobs/dag/
        """

        if job_id is None:
            jobsubConfig = JobsubConfig()
            logger.log('dag.py:doPost:kwargs: %s' % kwargs)
            jobsub_args = kwargs.get('jobsub_args_base64')
            jobsub_client_version = kwargs.get('jobsub_client_version')
            if jobsub_args is not None:

                jobsub_args = base64.urlsafe_b64decode(str(jobsub_args)).rstrip()
                logger.log('jobsub_args: %s' % jobsub_args)
                jobsub_command = kwargs.get('jobsub_command')
                jobsub_payload = kwargs.get('jobsub_payload')
                role  = kwargs.get('role')
                logger.log('dag.py:doPost:jobsub_command %s' %(jobsub_command))
                logger.log('dag.py:doPost:role %s ' % (role))
                #subject_dn = cherrypy.request.headers.get('Auth-User')

                command_path_acctgroup = jobsubConfig.commandPathAcctgroup(acctgroup)
                mkdir_p(command_path_acctgroup)
                command_path_user = jobsubConfig.commandPathUser(acctgroup,
                                                                 self.username)
                # Check if the user specific dir exist with correct
                # ownership. If not create it.
                jobsubConfig.initCommandPathUser(acctgroup, self.username)

                ts = datetime.now().strftime("%Y-%m-%d_%H%M%S.%f")
                uniquer=random.randrange(0,10000)
                workdir_id = '%s_%s' % (ts, uniquer)
                command_path = os.path.join(command_path_acctgroup, 
                                            self.username, workdir_id)
                logger.log('command_path: %s' % command_path)
                os.environ['X509_USER_PROXY'] = x509_proxy_fname(self.username,
                                                                 acctgroup, role)
                os.environ['JOBSUB_PAYLOAD'] = self.payLoadFileName
                # Create the job's working directory as user
                create_dir_as_user(command_path_user, workdir_id,
                                   self.username, mode='755')
                if jobsub_command is not None:
                    os.chdir(command_path)
                    command_file_path = os.path.join(command_path,
                                                     jobsub_command.filename)
                    payload_file_path = os.path.join(command_path,
                                                     jobsub_payload.filename)
                    os.environ['JOBSUB_COMMAND_FILE_PATH']=command_file_path
                    cf_path_w_space = ' %s'%command_file_path
                    logger.log('command_file_path: %s' % command_file_path)
                    logger.log('payload_file_path: %s' % payload_file_path)
                    payload_dest = os.path.join(command_file_path,
                                                self.payLoadFileName)
                    # First create a tmp file before moving the command file
                    # in place as correct user under the jobdir
                    tmp_file_prefix = os.path.join(jobsubConfig.tmpDir,
                                                   self.payLoadFileName)
                    tmp_payload_fd = NamedTemporaryFile(
                                         prefix="%s_"%tmp_file_prefix,
                                         delete=False)
                    copyfileobj(jobsub_payload.file, tmp_payload_fd)

                    tmp_payload_fd.close()
                    move_file_as_user(tmp_payload_fd.name, payload_file_path,
                                      self.username)

                    logger.log('before: jobsub_args = %s'%jobsub_args)
                    logger.log("cf_path_w_space='%s'"%cf_path_w_space)
                    command_tag = "\@(\S*)%s" % jobsub_command.filename
                    logger.log("command_tag='%s'"%command_tag)
                    logger.log('executing:"re.sub(command_tag, cf_path_w_space, jobsub_args)"')
                    jobsub_args = re.sub(command_tag, cf_path_w_space,
                                         str(jobsub_args))
                    logger.log('jobsub_args (subbed): %s' % jobsub_args)

                jobsub_args = jobsub_args.strip().split(' ')

                rc = execute_job_submit_wrapper(
                         acctgroup=acctgroup, username=self.username,
                         jobsub_args=jobsub_args, workdir_id=workdir_id,
                         role=role, jobsub_client_version=jobsub_client_version,
                         submit_type='dag')

            else:
                # return an error because no command was supplied
                err = 'User must supply jobsub command'
                logger.log(err)
                rc = {'err': err}
        else:
            # return an error because job_id has been supplied
            # but POST is for creating new jobs
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
            err = 'Exception on DagResource.index'
            cherrypy.response.status = 500
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc

