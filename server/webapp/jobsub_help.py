import cherrypy
import logger
import uuid
import os
import sys
import socket

from util import get_uid
from auth import check_auth
from job import AccountJobsResource
from format import format_response
from jobsub import get_supported_accountinggroups
from jobsub import execute_jobsub_command
from jobsub import get_dropbox_path_root
from util import mkdir_p
from util import digest_for_file
from users import UsersResource
from dropbox import DropboxResource

from cherrypy.lib.static import serve_file

from shutil import copyfileobj, rmtree


class JobsubHelpResource(object):
    def doGET(self, acctgroup):
        """ Executes the jobsub tools command with the help argument and returns the output.
            API call is /jobsub/acctgroups/<group_id>/help
        """
        jobsub_args = ['--help']
        subject_dn = cherrypy.request.headers.get('Auth-User')
        uid = get_uid(subject_dn)
        rc = execute_jobsub_command(acctgroup, uid, jobsub_args)

        return rc


    @cherrypy.expose
    @format_response
    def index(self, acctgroup, **kwargs):
        try:
            subject_dn = cherrypy.request.headers.get('Auth-User')
            if subject_dn is not None:
                logger.log('subject_dn: %s' % subject_dn)
                if cherrypy.request.method == 'GET':
                    rc = self.doGET(acctgroup)
                else:
                    err = 'Unsupported method: %s' % cherrypy.request.method
                    logger.log(err)
                    rc = {'err': err}
            else:
                # return error for no subject_dn
                err = 'User has not supplied subject dn'
                logger.log(err)
                rc = {'err': err}
        except :
            err = 'Exception on JobsubHelpResource.index %s'% sys.exc_info()[1]
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc



