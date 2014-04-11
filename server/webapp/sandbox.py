import os
import cherrypy
import logger
import math
from util import encode_multipart_formdata

from cherrypy.lib.static import serve_file

from util import get_uid, mkdir_p, create_zipfile
from auth import check_auth, get_x509_proxy_file
from jobsub import is_supported_accountinggroup, execute_jobsub_command, get_command_path_root
from format import format_response
from condor_commands import api_condor_q


condor_job_status = {
    1: 'Idle',
    2: 'Running',
    3: 'Removed',
    4: 'Completed',
    5: 'Held',
    6: 'Transferring Output',
}




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
            all_jobs = api_condor_q(acctgroup, uid)
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


