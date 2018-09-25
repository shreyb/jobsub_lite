"""
 Description:
   This module implements jobsub_q --long, --dag

 Project:
   JobSub

 Author:
   Dennis Box

 TODO:
   jobsub_q -af 'some fields' should go here at relatively low cost
"""
import cherrypy
import logger
import logging
import sys
import request_headers

from condor_commands import ui_condor_q, constructFilter
from format import format_response


class QueuedFormattedOutputResource(object):

    def __init__(self):
        cherrypy.response.status = 501

    def doGET(self, fmt, kwargs):
        cherrypy.response.status = 200
        acctgroup = kwargs.get('acctgroup', None)
        user_id = kwargs.get('user', None)
        job_id = kwargs.get('job_id', None)
        my_filter = constructFilter(acctgroup, user_id, job_id)
        logger.log("filter=%s" % my_filter)
        user_jobs = ui_condor_q(my_filter, fmt)
        return {'out': user_jobs.split('\n')}

    @cherrypy.expose
    @format_response(output_format='pre')
    def index(self, **kwargs):
        cherrypy.response.status = 501
        try:
            if cherrypy.request.method == 'GET':
                fmt = request_headers.path_end()
                rc = self.doGET(fmt, kwargs)
            else:
                err = 'Unimplemented method: %s' % cherrypy.request.method
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rc = {'err': err}
        except Exception:
            err = 'Exception on QueuedLongResouce.index: %s' % sys.exc_info()[
                1]
            cherrypy.response.status = 500
            logger.log(err, traceback=True, severity=logging.ERROR)
            logger.log(err,
                       traceback=True,
                       severity=logging.ERROR,
                       logfile='error')
            rc = {'err': err}

        return rc
