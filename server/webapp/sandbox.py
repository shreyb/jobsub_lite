import os
import cherrypy
import logger
import math
from util import encode_multipart_formdata

from cherrypy.lib.static import serve_file

from util import get_uid, mkdir_p, create_zipfile, create_tarfile
from auth import check_auth
from jobsub import is_supported_accountinggroup, execute_jobsub_command, get_command_path_root
from format import format_response
from condor_commands import api_condor_q
from datetime import datetime


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


class SandboxResource(object):
    """ Download compressed output sandbox for a given job
        API is /jobsub/acctgroups/<group_id>/jobs/<job_id>/sandbox/
    """


    #@format_response
    def doGET(self, acctgroup, job_id, kwargs):
	logger.log(kwargs)
        subject_dn = cherrypy.request.headers.get('Auth-User')
        uid = get_uid(subject_dn)
        command_path_root = get_command_path_root()
        if job_id is None:
            job_tokens = ['0']
        else:
            job_tokens = job_id.split('.')
        job_id = '%s.0' % job_tokens[0]
        zip_path = os.path.join(command_path_root, acctgroup, uid, job_id)
        if os.path.exists(zip_path):
            ts = datetime.now().strftime("%Y-%m-%d_%H%M%S.%f")
            format=kwargs.get('archive_format')
            logger.log('archive_format:%s'%format)
            if format and format=='zip':
                zip_file = os.path.join(command_path_root, acctgroup, uid, '%s.%s.zip'%(job_tokens[0],ts))
                create_zipfile(zip_file, zip_path, job_id)
            else:           
                zip_file = os.path.join(command_path_root, acctgroup, uid, '%s.%s.tgz'%(job_tokens[0],ts))
                create_tarfile(zip_file, zip_path, job_id)

            rc = {'out': zip_file}

            cherrypy.request.hooks.attach('on_end_request', cleanup, zip_file=zip_file)
            logger.log('returning %s'%zip_file)
            return serve_file(zip_file, 'application/x-download','attachment')

        else:
            # return error for no data found
            err = 'No sandbox data found for user: %s, acctgroup: %s, job_id %s' % (uid, acctgroup, job_id)
            logger.log(err)
            #rc = {'err': err}
            cherrypy.response.status = 404
            jobs_file_path = os.path.join(command_path_root, acctgroup, uid)
            sandbox_cluster_ids = list()
            if os.path.exists(jobs_file_path):
		logger.log('walking %s'%jobs_file_path)
                dirs=os.listdir(jobs_file_path)
                for dir in dirs:
                    if os.path.islink(os.path.join(jobs_file_path, dir)):
			frag="""<a href="../../%s/sandbox/">%s</a>"""%(dir,dir)
                        sandbox_cluster_ids.append(frag)
                sandbox_cluster_ids.sort()
	    outmsg = "For user %s, accounting group %s, the server can retrieve information for these job_ids:"% (uid,acctgroup)
	    sandbox_cluster_ids.insert(0,outmsg)
            rc = {'out': sandbox_cluster_ids , 'err':err }

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
            err = 'Exception on SandboxResource.index'
            logger.log(err, traceback=True)
            rc = {'err': err}
            cherrypy.response.status = 500
  
        return rc


