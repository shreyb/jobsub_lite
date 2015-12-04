import os
import cherrypy
import logger
import re

from cherrypy.lib.static import serve_file

from util import create_zipfile, create_tarfile
from auth import check_auth
from jobsub import is_supported_accountinggroup, get_command_path_root, sandbox_readable_by_group
from jobsub import JobsubConfig
from jobsub import run_cmd_as_user
from format import format_response
from datetime import datetime
from JobsubConfigParser import JobsubConfigParser
from condor_commands import constructFilter, iwd_condor_q
from sqlite_commands import constructQuery, iwd_jobsub_history





def cleanup(zip_file, outfilename=None):
    """ Hook function to cleanup sandbox files after request has been processed
    """
             
    if outfilename is not None:
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


def make_sandbox_readable(workdir, username):
    cmd = [
        'chmod',
        '-R',
        '+r',
        os.path.realpath(workdir)
    ]

    out, err = run_cmd_as_user(cmd, username, child_env=os.environ.copy())


def create_archive(zip_file, zip_path, job_id, out_format, partial=None):
    if out_format=='tgz':
        create_tarfile(zip_file, zip_path, job_id, partial=partial)
    else:
        create_zipfile(zip_file, zip_path, job_id, partial=partial)
        


@cherrypy.popargs('partial')
class SandboxResource(object):
    """ Download compressed output sandbox for a given job
        API is /jobsub/acctgroups/<group_id>/jobs/<job_id>/sandbox/
    """

    def __init__(self):
        cherrypy.request.role = None
        cherrypy.request.username = None
        cherrypy.request.vomsProxy = None


    def findSandbox(self, path):
        if not path:
            return False
        if os.path.exists(path):
            return path 
        return False



    #@format_response
    def doGET(self, acctgroup, job_id, partial=None,  **kwargs):
        # set cherrypy.response.timeout to something bigger than 300 seconds
        timeout = 60*15
        try:
            p = JobsubConfigParser()
            t = p.get('default', 'sandbox_timeout')
            if t is not None:
                timeout = t
        except Exception, e:
            logger.log('caught %s  setting default timeout'%e)

        cherrypy.response.timeout = timeout
        logger.log('sandbox timeout=%s' % cherrypy.response.timeout)
        logger.log('partial=%s' % partial)
        jobsubConfig = JobsubConfig()
        sbx_create_dir = jobsubConfig.commandPathAcctgroup(acctgroup)
        sbx_final_dir = jobsubConfig.commandPathUser(acctgroup, cherrypy.request.username)

        command_path_root = get_command_path_root()
        if job_id is None:
             job_id = 'I_am_planning_on_failing'
        zip_path = os.path.join(sbx_final_dir, job_id)
        zip_path = self.findSandbox(os.path.join(sbx_final_dir, job_id))
        if partial or not zip_path:
            #it might be a valid jobsubjobid that is part of a dag or non zero ProcessID
            zip_path = None
            try:
                query = constructFilter(jobid=job_id)
                zip_path = iwd_condor_q(query)
                if partial:
                    cmd = iwd_condor_q(query,'cmd')
                    logger.log('cmd=%s'%cmd)
                    expr = '^(\S+)(_\d+_\d+_\d+_\d+_\d+_)(\S+)*'
                    regex = re.compile(expr)
                    g = regex.match(cmd)
                    partial = g.group(2) 
                    logger.log('partial=%s'%partial)

                logger.log('zip_path from condor_q:%s' % zip_path)
            except Exception, e:
                logger.log('%s'%e)
        if not zip_path:
            try:
                query = constructQuery(jobid=job_id)
                zip_path = iwd_jobsub_history(query)
                logger.log('zip_path from jobsub_history:%s' % zip_path)
                if partial:
                    cmd = iwd_jobsub_history(query,'ownerjob')
                    logger.log('cmd=%s'%cmd)
                    expr = '^(\S+)(_\d+_\d+_\d+_\d+_\d+_)(\S+)*'
                    regex = re.compile(expr)
                    g = regex.match(cmd)
                    partial = g.group(2) 
                    logger.log('partial=%s'%partial)


            except Exception, e:
                logger.log('%s'%e)
        logger.log('zip_path=%s'%zip_path)
        if zip_path:
            zip_path=zip_path.rstrip()
            zip_path=zip_path.lstrip()
        if zip_path and os.path.exists(zip_path):
            ts = datetime.now().strftime("%Y-%m-%d_%H%M%S.%f")
            out_format = kwargs.get('archive_out_format', 'tgz')
            logger.log('archive_out_format:%s'%out_format)
            zip_file_tmp = None
            if out_format not in ('zip', 'tgz'):
                out_format = 'tgz'

            # Moving the file to user dir and changing the ownership
            # prevents cherrypy from doing the cleanup. Keep the files in
            # in acctgroup area to allow for cleanup
            zip_file = os.path.join(sbx_create_dir,
                                        '%s.%s.%s' % (job_id, ts, out_format))
            rc = {'out': zip_file}

            cherrypy.request.hooks.attach('on_end_request', cleanup,
                                          zip_file=zip_file)
            cherrypy.request.hooks.attach('after_error_response', cleanup,
                                          zip_file=zip_file)
            owner = os.path.basename(os.path.dirname(zip_path))
            if owner != cherrypy.request.username:
                if sandbox_readable_by_group(acctgroup):
                    make_sandbox_readable(zip_path, owner)
                else:
                    err = "User %s is not allowed  to read %s, owned by %s on this server.  "%(cherrypy.request.username,job_id,owner)
                    err += "This is configurable, if you believe this to be in error please open a service desk ticket."
                    cherrypy.response.status = 500
                    rc = {'err':err}
                    return rc

            create_archive(zip_file, zip_path, job_id, out_format, partial=partial)
            logger.log('returning %s'%zip_file)
            return serve_file(zip_file, 'application/x-download', 'attachment')

        else:
            # TO:DO: PM
            # Do we need this logic anymore? fetchlog now supports a much
            # cleaner option --list-sandboxes
            # return error for no data found
            cherrypy.response.status = 404
            outmsg = """
                Information for job %s not found.  Make sure that you specified the appropriate Role for this job. The role must be the same as what it was for submission.  If you used jobsub_q or jobsub_history to find this job ID, double check that you specified --group incorrectly.  If the job is more than a few weeks old, it was probably removed to save space. Jobsub_fetchlog --list will show the  sandboxes that are still on the server."""  %job_id
            rc = {'err': outmsg}

        return rc

    @cherrypy.expose
    @format_response
    @check_auth
    def index(self, acctgroup, job_id, partial=None, **kwargs):
        logger.log('job_id:%s'%job_id)
        logger.log('partial:%s'%partial)
        logger.log('kwargs:%s'%kwargs)
        cherrypy.request.role = kwargs.get('role')
        cherrypy.request.username = kwargs.get('username')
        cherrypy.request.vomsProxy = kwargs.get('voms_proxy')

        try:
            if job_id is None:
                raise

            if is_supported_accountinggroup(acctgroup):
                if cherrypy.request.method == 'GET':
                    rc = self.doGET(acctgroup, job_id, partial, **kwargs)
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
            err = 'Exception on SandboxResource.index'
            cherrypy.response.status = 500
            logger.log(err, traceback=True)
            rc = {'err': err}
            cherrypy.response.status = 500
  
        return rc


