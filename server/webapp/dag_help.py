
"""Module:
        dag_help
   Purpose:
        displays help file from
        original jobsub tools dag generator.
        API is /jobsub/acctgroups/<group_id>/jobs/dag/help/
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


class DAGHelpResource(object):

    def doGET(self, acctgroup):
        """
        displays help file from
        original jobsub tools dag generator.
        API is /jobsub/acctgroups/<group_id>/jobs/dag/help/
        """
        jobsub_args = ['-manual']
        rcode = execute_job_submit_wrapper(acctgroup, None, jobsub_args,
                                           submit_type='dag', priv_mode=False)

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
            err = 'Exception on DAGHelpResource.index %s' % sys.exc_info()[1]
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
            rcode = {'err': err}

        return rcode
