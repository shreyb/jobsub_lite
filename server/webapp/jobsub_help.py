""" Module:
            jobsub_help
    Purpose:
            displays help file from
            original jobsub tools job submitter
            API is /jobsub/acctgroups/<group_id>/help/
    Author:
            Dennis Box
"""
import cherrypy
import logger
import logging
import sys

from request_headers import get_client_dn
from format import format_response
from jobsub import execute_job_submit_wrapper


class JobsubHelpResource(object):

    def doGET(self, acctgroup):
        """ Executes the jobsub tools command with the help argument and
            returns the output.
            API call is /jobsub/acctgroups/<group_id>/help
        """
        jobsub_args = ['--help']
        rcode = execute_job_submit_wrapper(acctgroup, None, jobsub_args,
                                           priv_mode=False)

        return rcode

    @cherrypy.expose
    @format_response(output_format='pre')
    def index(self, acctgroup, **kwargs):
        try:
            subject_dn = get_client_dn()
            if subject_dn is not None:
                logger.log('subject_dn: %s' % subject_dn)
                if cherrypy.request.method == 'GET':
                    rcode = self.doGET(acctgroup)
                else:
                    err = 'Unsupported method: %s' % cherrypy.request.method
                    logger.log(err, severity=logging.ERROR)
                    logger.log(err, severity=logging.ERROR, logfile='error')
                    rcode = {'err': err}
            else:
                # return error for no subject_dn
                err = 'User has not supplied subject dn'
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rcode = {'err': err}
        except:
            err = 'Exception on JobsubHelpResource.index %s' % sys.exc_info()[
                1]
            cherrypy.response.status = 500
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
            rcode = {'err': err}

        return rcode
