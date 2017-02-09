"""Module:
        dag
   Purpose:
        Create/Submit a new dag. Returns the output from
        original jobsub tools dag generator.
        API is /jobsub/acctgroups/<group_id>/jobs/dag/
   Author:
        Nick Palumbo
"""
import base64
import random
import os
import re
import cherrypy
import logger
import logging
import request_headers

from datetime import datetime
from shutil import copyfileobj


from tempfile import NamedTemporaryFile

from util import mkdir_p
from auth import check_auth
from authutils import x509_proxy_fname
from jobsub import is_supported_accountinggroup
from jobsub import JobsubConfig
from jobsub import execute_job_submit_wrapper
from jobsub import create_dir_as_user
from jobsub import move_file_as_user

from format import format_response
from dag_help import DAGHelpResource


@cherrypy.popargs('job_id')
class DagResource(object):

    def __init__(self):
        self.help = DAGHelpResource()
        self.payload_filename = 'payload.tgz'

    def doPOST(self, acctgroup, job_id, kwargs):
        """ Create/Submit a new dag. Returns the output from
            original jobsub tools dag generator.
            API is /jobsub/acctgroups/<group_id>/jobs/dag/
        """

        if job_id is None:
            jscfg = JobsubConfig()
            logger.log('dag.py:doPost:kwargs: %s' % kwargs)
            jobsub_args = kwargs.get('jobsub_args_base64')
            jobsub_client_version = kwargs.get('jobsub_client_version')
            jobsub_client_krb5_principal = kwargs.get(
                'jobsub_client_krb5_principal', 'UNKNOWN')
            child_env = os.environ.copy()
            if jobsub_args is not None:

                jobsub_args = base64.urlsafe_b64decode(
                    str(jobsub_args)).rstrip()
                logger.log('jobsub_args: %s' % jobsub_args)
                jobsub_command = kwargs.get('jobsub_command')
                jobsub_payload = kwargs.get('jobsub_payload')
                role = kwargs.get('role')
                logger.log('dag.py:doPost:jobsub_command %s' %
                           (jobsub_command))
                logger.log('dag.py:doPost:role %s ' % (role))

                command_path_acctgroup = jscfg.commandPathAcctgroup(acctgroup)
                mkdir_p(command_path_acctgroup)
                uname = None
                try:
                    uname = cherrypy.request.username
                except:
                    uname = request_headers.uid_from_client_dn()

                command_path_user = jscfg.commandPathUser(acctgroup,
                                                          uname)
                # Check if the user specific dir exist with correct
                # ownership. If not create it.
                jscfg.initCommandPathUser(acctgroup, uname)

                tstmp = datetime.now().strftime("%Y-%m-%d_%H%M%S.%f")
                uniquer = random.randrange(0, 10000)
                workdir_id = '%s_%s' % (tstmp, uniquer)
                command_path = os.path.join(command_path_acctgroup,
                                            uname,
                                            workdir_id)
                logger.log('command_path: %s' % command_path)
                child_env['X509_USER_PROXY'] = x509_proxy_fname(uname,
                                                                acctgroup,
                                                                role)
                child_env['JOBSUB_PAYLOAD'] = self.payload_filename
                # Create the job's working directory as user
                create_dir_as_user(command_path_user, workdir_id,
                                   uname, mode='755')
                if jobsub_command is not None:
                    os.chdir(command_path)
                    command_file_path = os.path.join(command_path,
                                                     jobsub_command.filename)
                    payload_file_path = os.path.join(command_path,
                                                     jobsub_payload.filename)
                    # os.environ['JOBSUB_COMMAND_FILE_PATH']=command_file_path
                    cf_path_w_space = ' %s' % command_file_path
                    logger.log('command_file_path: %s' % command_file_path)
                    logger.log('payload_file_path: %s' % payload_file_path)
                    # First create a tmp file before moving the command file
                    # in place as correct user under the jobdir
                    tmp_file_prefix = os.path.join(jscfg.tmp_dir,
                                                   self.payload_filename)
                    tmp_payload_fd = NamedTemporaryFile(
                        prefix="%s_" % tmp_file_prefix,
                        delete=False)
                    copyfileobj(jobsub_payload.file, tmp_payload_fd)

                    tmp_payload_fd.close()
                    move_file_as_user(tmp_payload_fd.name, payload_file_path,
                                      uname)

                    logger.log('before: jobsub_args = %s' % jobsub_args)
                    logger.log("cf_path_w_space='%s'" % cf_path_w_space)
                    command_tag = "\@(\S*)%s" % jobsub_command.filename
                    logger.log("command_tag='%s'" % command_tag)
                    _str = '"re.sub(command_tag, cf_path_w_space, jobsub_args)"'
                    logger.log('executing:%s' % _str)
                    jobsub_args = re.sub(command_tag, cf_path_w_space,
                                         str(jobsub_args))
                    logger.log('jobsub_args (subbed): %s' % jobsub_args)

                jobsub_args = jobsub_args.strip().split(' ')

                rcode = execute_job_submit_wrapper(
                    acctgroup=acctgroup, username=uname,
                    jobsub_args=jobsub_args, workdir_id=workdir_id,
                    role=role, jobsub_client_version=jobsub_client_version,
                    jobsub_client_krb5_principal=jobsub_client_krb5_principal,
                    submit_type='dag', child_env=child_env)

                if rcode.get('out'):
                    for line in rcode['out']:
                        if 'jobsubjobid' in line.lower():
                            logger.log(line)
                if rcode.get('err'):
                    logger.log(rcode['err'], severity=logging.ERROR)
                    logger.log(rcode['err'], severity=logging.ERROR,
                               logfile='error')
            else:
                # return an error because no command was supplied
                err = 'User must supply jobsub command'
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rcode = {'err': err}
        else:
            # return an error because job_id has been supplied
            # but POST is for creating new jobs
            err = 'User has supplied job_id but POST is for creating new jobs'
            logger.log(err, severity=logging.ERROR)
            logger.log(err, severity=logging.ERROR, logfile='error')
            rcode = {'err': err}
        if rcode.get('err'):
            cherrypy.response.status = 500
        return rcode

    @cherrypy.expose
    @format_response
    def default(self, kwargs):
        logger.log('kwargs=%s' % kwargs)
        return {'out': "kwargs=%s" % kwargs}

    @cherrypy.expose
    @format_response
    @check_auth
    def index(self, acctgroup, job_id=None, **kwargs):
        try:
            cherrypy.request.role = kwargs.get('role')
            cherrypy.request.vomsProxy = kwargs.get('voms_proxy')
            #cherrypy.request.username should be set by @check_auth using GUMS
            #but double check
            if not hasattr(cherrypy.request, 'username') or \
                    not cherrypy.request.username:
                cherrypy.request.username = kwargs.get('username')
            if is_supported_accountinggroup(acctgroup):
                if cherrypy.request.method == 'POST':
                    rcode = self.doPOST(acctgroup, job_id, kwargs)
                else:
                    err = 'Unsupported method: %s' % cherrypy.request.method
                    logger.log(err, severity=logging.ERROR)
                    logger.log(err, severity=logging.ERROR, logfile='error')
                    rcode = {'err': err}
            else:
                # return error for unsupported acctgroup
                err = 'AccountingGroup %s ' % acctgroup
                err += 'is not configured in jobsub'
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rcode = {'err': err}
        except:
            err = 'Exception on DagResource.index'
            cherrypy.response.status = 500
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
            rcode = {'err': err}

        return rcode
