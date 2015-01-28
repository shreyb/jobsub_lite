import cherrypy
import logger
import uuid
import os
import sys
import socket

from util import get_uid
from auth import check_auth
from format import format_response
from jobsub import execute_job_submit_wrapper




class JobsubHelpResource(object):
    def doGET(self, acctgroup):
        """ Executes the jobsub tools command with the help argument and returns the output.
            API call is /jobsub/acctgroups/<group_id>/help
        """
        jobsub_args = ['--help']
        subject_dn = cherrypy.request.headers.get('Auth-User')
        rc = execute_job_submit_wrapper(acctgroup, None, jobsub_args,
                                        priv_mode=False)

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
            cherrypy.response.status = 500
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc



