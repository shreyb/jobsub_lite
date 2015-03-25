import os
import cherrypy
import logger
import math
import subprocessSupport

from cherrypy.lib.static import serve_file

from util import create_zipfile, create_tarfile
from auth import check_auth
from jobsub import is_supported_accountinggroup, get_command_path_root
from jobsub import JobsubConfig
from jobsub import move_file_as_user
from jobsub import run_cmd_as_user
from format import format_response
from datetime import datetime
from JobsubConfigParser import JobsubConfigParser

condor_job_status = {
    1: 'Idle',
    2: 'Running',
    3: 'Removed',
    4: 'Completed',
    5: 'Held',
    6: 'Transferring Output',
}




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


def create_archive(zip_file, zip_path, job_id, format):
    if format=='tgz':
        create_tarfile(zip_file, zip_path, job_id)
    else:
        create_zipfile(zip_file, zip_path, job_id)
        


class SandboxResource(object):
    """ Download compressed output sandbox for a given job
        API is /jobsub/acctgroups/<group_id>/jobs/<job_id>/sandbox/
    """

    def __init__(self):
        cherrypy.request.role = None
        cherrypy.request.username = None
        cherrypy.request.vomsProxy = None


    def findSandbox(self, path):
	if os.path.exists(path):
	    return path
	jobid=os.path.basename(path)
	logger.log('jobid:%s'%jobid)
	uid = '/%s/' % cherrypy.request.username
        cmd1=""" -format '%s' iwd -constraint """ 
        cmd2="""'jobsubjobid=="%s"' """%(jobid)
	for cmd0 in ['condor_history ','condor_q ']:
            cmd=cmd0+cmd1+cmd2
            logger.log(cmd)
            newpath, cmd_err = subprocessSupport.iexe_cmd(cmd)
            logger.log('result:%s status:%s'%(newpath,cmd_err))
            if newpath and len(newpath)>0 and os.path.exists(newpath) and (uid in newpath):
                return newpath
        return False


    #@format_response
    def doGET(self, acctgroup, job_id, kwargs):
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
        jobsubConfig = JobsubConfig()
        sbx_create_dir = jobsubConfig.commandPathAcctgroup(acctgroup)
        sbx_final_dir = jobsubConfig.commandPathUser(acctgroup, cherrypy.request.username)

        command_path_root = get_command_path_root()
        if job_id is None:
             job_id='I_am_planning_on_failing'
        #zip_path = os.path.join(sbx_final_dir, job_id)
	zip_path = self.findSandbox(os.path.join(sbx_final_dir, job_id))
        if zip_path:
            ts = datetime.now().strftime("%Y-%m-%d_%H%M%S.%f")
            format = kwargs.get('archive_format', 'tgz')
            logger.log('archive_format:%s'%format)
            zip_file_tmp = None
            if format not in ('zip', 'tgz'):
                format = 'tgz'

            # Moving the file to user dir and changing the ownership
            # prevents cherrypy from doing the cleanup. Keep the files in
            # in acctgroup area to allow for cleanup
            zip_file = os.path.join(sbx_create_dir,
                                        '%s.%s.%s' % (job_id, ts, format))
            rc = {'out': zip_file}

            cherrypy.request.hooks.attach('on_end_request', cleanup,
                                          zip_file=zip_file)
            cherrypy.request.hooks.attach('after_error_response', cleanup,
                                          zip_file=zip_file)

            make_sandbox_readable(zip_path, cherrypy.request.username)
            create_archive(zip_file, zip_path, job_id, format)
            logger.log('returning %s'%zip_file)
            return serve_file(zip_file, 'application/x-download','attachment')

        else:
            # TODO: PM
            # Do we need this logic anymore? fetchlog now supports a much
            # cleaner option --list-sandboxes
            # return error for no data found
            cherrypy.response.status = 404
            sandbox_cluster_ids = list()
            if os.path.exists(sbx_final_dir):
		logger.log('Looking for available sandboxes %s'%sbx_final_dir)
                dirs = os.listdir(sbx_final_dir)
                for dir in dirs:
                    if os.path.islink(os.path.join(sbx_final_dir, dir)) and dir.find('@')>0:
                        frag="""%s"""%(dir)
                        sandbox_cluster_ids.append(frag)
                sandbox_cluster_ids.sort()

            if sandbox_cluster_ids:
                outmsg = "For user %s, accounting group %s, the server can retrieve information for these job_ids:"% (cherrypy.request.username ,acctgroup)
                sandbox_cluster_ids.insert(0,outmsg)
                rc = {'out': sandbox_cluster_ids }
            else:
                err = 'No sandbox data found for user: %s, acctgroup: %s, job_id %s' % (cherrypy.request.username , acctgroup, job_id)
                rc = {'err':err }

        return rc

    @cherrypy.expose
    @format_response
    @check_auth
    def index(self, acctgroup, job_id, **kwargs):
        logger.log('job_id:%s'%job_id)
        cherrypy.request.role = kwargs.get('role')
        cherrypy.request.username = kwargs.get('username')
        cherrypy.request.vomsProxy = kwargs.get('voms_proxy')

        try:
            if job_id is None:
                raise

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
            err = 'Exception on SandboxResource.index'
            cherrypy.response.status = 500
            logger.log(err, traceback=True)
            rc = {'err': err}
            cherrypy.response.status = 500
  
        return rc


