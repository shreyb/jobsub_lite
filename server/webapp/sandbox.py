"""
 Description:
   This module implements the jobsub_fetchlog command

 Project:
   JobSub

 Author:
   Nick Palumbo

 TODO:
   implement cacheing so that if someone requests the same
   sandbox a bunch of times in a row it just gets one and
   doesnt tank the server tarring up the sandbox
"""
import os
import cherrypy
import logger
import logging
import re
import time

from cherrypy.lib.static import serve_file

from util import create_zipfile
from util import create_tarfile
from auth import check_auth
from jobsub import is_supported_accountinggroup
from jobsub import sandbox_readable_by_group
from jobsub import is_superuser_for_group
from jobsub import is_global_superuser
from jobsub import JobsubConfig
from jobsub import run_cmd_as_user
from format import format_response
from datetime import datetime
from JobsubConfigParser import JobsubConfigParser
from condor_commands import constructFilter
from condor_commands import iwd_condor_q
from sqlite_commands import constructQuery
from sqlite_commands import iwd_jobsub_history
from request_headers import uid_from_client_dn

def cleanup(zip_file, outfilename=None):
    """ Hook function to cleanup sandbox files after request has been processed
    """

    if outfilename is not None:
        try:
            os.remove(outfilename)
        except:
            err = 'Failed to remove encoded file at %s' % outfilename
            logger.log(err)
            logger.log(err, severity=logging.ERROR, logfile='error')
    try:
        os.remove(zip_file)
    except:
        err = 'Failed to remove zip file at %s' % zip_file
        logger.log(err)
        logger.log(err, severity=logging.ERROR, logfile='error')


def make_sandbox_readable(workdir, username):
    """
    change file permissions on sandbox, see 'cmd'
    """
    cmd = [
        'chmod',
        '-R',
        '+r',
        os.path.realpath(workdir)
    ]

    out, err = run_cmd_as_user(cmd, username, child_env=os.environ.copy())


def create_archive(zip_file, zip_path, job_id, out_format, partial=None):
    """
    create a tar or zip file depending on outformat
    """
    if out_format == 'tgz':
        create_tarfile(zip_file, zip_path, job_id, partial=partial)
    else:
        create_zipfile(zip_file, zip_path, job_id, partial=partial)


@cherrypy.popargs('partial')
class SandboxResource(object):
    """ Download compressed output sandbox for a given job
        API is /jobsub/acctgroups/<group_id>/jobs/<job_id>/sandbox/
    """


    def findSandbox(self, path):
        """
        check that sandbox exists
        """
        if not path:
            return False
        if os.path.exists(path):
            return path
        return False

    #@format_response
    def doGET(self, acctgroup, job_id, partial=None, **kwargs):
        """
        perform http get
        """
        # set cherrypy.response.timeout to something bigger than 300 seconds
        timeout = 60 * 15
        try:
            request_uid = cherrypy.request.username
        except:
            request_uid = uid_from_client_dn()
        if not request_uid:
            request_uid = kwargs.get('username')
        prs = JobsubConfigParser()
        try:
            tim = prs.get('default', 'sandbox_timeout')
            if tim is not None:
                timeout = tim
        except Exception as excp:
            logger.log('caught %s  setting default timeout' % excp)
            logger.log('caught %s  setting default timeout' % excp,
                       severity=logging.ERROR,
                       logfile='error')

        cherrypy.response.timeout = timeout
        logger.log('sandbox timeout=%s' % cherrypy.response.timeout)
        logger.log('partial=%s' % partial)
        jobsubConfig = JobsubConfig()
        sbx_create_dir = jobsubConfig.commandPathAcctgroup(acctgroup)
        sbx_final_dir = jobsubConfig.commandPathUser(acctgroup,
                                                     request_uid)

        if job_id is None:
            job_id = 'I_am_planning_on_failing'
        zip_path = os.path.join(sbx_final_dir, job_id)
        zip_path = self.findSandbox(os.path.join(sbx_final_dir, job_id))
        if partial or not zip_path:
            # it might be a valid jobsubjobid that is part of a dag or non zero
            # ProcessID
            zip_path = None
            try:
                query = constructFilter(jobid=job_id)
                zip_path = iwd_condor_q(query)
                if partial:
                    cmd = iwd_condor_q(query, 'cmd')
                    logger.log('cmd=%s' % cmd)
                    expr = '^(\S+)(_\d+_\d+_\d+_\d+_\d+_)(\S+)*'
                    regex = re.compile(expr)
                    g = regex.match(cmd)
                    partial = g.group(2)
                    logger.log('partial=%s' % partial)

                logger.log('zip_path from condor_q:%s' % zip_path)
            except Exception as excp:
                logger.log('%s' % excp)
                logger.log('%s' % excp,
                           severity=logging.ERROR,
                           logfile='error')
        if not zip_path:
            try:
                query = constructQuery(jobid=job_id)
                zip_path = iwd_jobsub_history(query)
                logger.log('zip_path from jobsub_history:%s' % zip_path)
                if partial:
                    cmd = iwd_jobsub_history(query, 'ownerjob')
                    logger.log('cmd=%s' % cmd)
                    expr = '^(\S+)(_\d+_\d+_\d+_\d+_\d+_)(\S+)*'
                    regex = re.compile(expr)
                    g = regex.match(cmd)
                    partial = g.group(2)
                    logger.log('partial=%s' % partial)

            except Exception as excp:
                logger.log('%s' % excp)
                logger.log('%s' % excp,
                           severity=logging.ERROR,
                           logfile='error')
        logger.log('zip_path=%s' % zip_path)
        if zip_path:
            zip_path = zip_path.rstrip()
            zip_path = zip_path.lstrip()
        if zip_path and os.path.exists(zip_path):
            #ts = datetime.now().strftime("%Y-%m-%d_%H%M%S.%f")
            out_format = kwargs.get('archive_out_format', 'tgz')
            logger.log('archive_out_format:%s' % out_format)
            if out_format not in ('zip', 'tgz'):
                out_format = 'tgz'

            # Moving the file to user dir and changing the ownership
            # prevents cherrypy from doing the cleanup. Keep the files in
            # in acctgroup area to allow for cleanup
            zip_file = os.path.join(sbx_create_dir,
                                    '%s.%s' % (job_id, out_format))
            if partial:
                zipfile="partial_%s" % zip_file
            rcode = {'out': zip_file}

            #cherrypy.request.hooks.attach('on_end_request', cleanup,
            #                              zip_file=zip_file)
            #cherrypy.request.hooks.attach('after_error_response', cleanup,
            #                              zip_file=zip_file)
            owner = os.path.basename(os.path.dirname(zip_path))
            if owner != request_uid:
                if sandbox_readable_by_group(acctgroup) \
                        or is_superuser_for_group(acctgroup,request_uid) \
                        or is_global_superuser(request_uid):
                    make_sandbox_readable(zip_path, owner)
                else:
                    err = "User %s is not allowed  to read %s, owned by %s." % (
                        request_uid, job_id, owner)
                    err += " This is configurable, if you believe this to be "
                    err += "in error please open a service desk ticket."
                    cherrypy.response.status = 500
                    rcode = {'err': err}
                    return rcode
            else:
                if self.valid_cached(zip_file):
                    return serve_file(zip_file, 'application/x-download', 'attachment')

                make_sandbox_readable(zip_path, owner)
            create_archive(zip_file, zip_path, job_id,
                           out_format, partial=partial)
            logger.log('returning %s' % zip_file)
            return serve_file(zip_file, 'application/x-download', 'attachment')

        else:
            # TO:DO: PM
            # Do we need this logic anymore? fetchlog now supports a much
            # cleaner option --list-sandboxes
            # return error for no data found
            cherrypy.response.status = 404
            outmsg = """
            Information for job %s not found.  Make sure that you specified
            the appropriate Role for this job. The role must be the same as
            what it was for submission.  If you used jobsub_q or jobsub_history
            to find this job ID, double check that you specified --group
            incorrectly.  If the job is more than a few weeks old, it was
            probably removed to save space. Jobsub_fetchlog --list will
            show the  sandboxes that are still on the server."""  % job_id
            rcode = {'err': ' '.join(outmsg.split())}

        return rcode

    def valid_cached(self, zip_file):
        rslt = False
        if os.path.exists(zip_file):
            stt = os.stat(zip_file)
            zip_age = (time.time() - stt.st_mtime)
            prs = JobsubConfigParser()
            max_age = prs.get('default', 'max_logfile_cache_age')
            if not max_age:
                max_age = 1200
            if zip_age < max_age:
                rslt = True
        return rslt

    @cherrypy.expose
    @format_response
    @check_auth
    def index(self, acctgroup, job_id, partial=None, **kwargs):
        """
        index.html for /jobsub/<acctgroup>/job/jobid/sandbox
        """
        logger.log('job_id:%s' % job_id)
        logger.log('partial:%s' % partial)
        logger.log('kwargs:%s' % kwargs)

        try:
            if job_id is None:
                raise

            if is_supported_accountinggroup(acctgroup):
                if cherrypy.request.method == 'GET':
                    rcode = self.doGET(acctgroup, job_id, partial, **kwargs)
                else:
                    err = 'Unsupported method: %s' % cherrypy.request.method
                    logger.log(err)
                    logger.log(err, severity=logging.ERROR, logfile='error')
                    rcode = {'err': err}
                    cherrypy.response.status = 500
            else:
                # return error for unsupported acctgroup
                err = 'AccountingGroup %s is not configured in jobsub' %\
                    acctgroup
                logger.log(err)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rcode = {'err': err}
                cherrypy.response.status = 500
        except:
            err = 'Exception on SandboxResource.index'
            cherrypy.response.status = 500
            logger.log(err, traceback=True)
            logger.log(err,
                       traceback=True,
                       severity=logging.ERROR,
                       logfile='error')
            rcode = {'err': err}
            cherrypy.response.status = 500

        return rcode
