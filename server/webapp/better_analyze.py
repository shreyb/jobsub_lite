"""Module:
        better_analyze
   Purpose:
        implement condor_q -better-analyze
        API is /jobsub/jobs/jobid/<jobid>/betteranalyze/
   Author:
        Dennis Box
"""

import cherrypy
import logger
import logging
import sys

from condor_commands import ui_condor_q, constructFilter
from format import format_response


@cherrypy.popargs('job_id')
class BetterAnalyzeResource(object):
    """Class Implementation of condor_q -better-analyze 'job_id'
    """

    def __init__(self):
        cherrypy.response.status = 501

    def doGET(self, job_id, kwargs):
        cherrypy.response.status = 200
        acctgroup = None
        user_id = None
        my_filter = constructFilter(acctgroup, user_id, job_id)
        logger.log("filter=%s" % my_filter)
        user_jobs = ui_condor_q(my_filter, 'better-analyze')
        return {'out': user_jobs.split('\n')}

    @cherrypy.expose
    @format_response
    def index(self, job_id, **kwargs):
        cherrypy.response.status = 501
        try:
            if cherrypy.request.method == 'GET':
                rcode = self.doGET(job_id, kwargs)
            else:
                err = 'Unimplemented method: %s' % cherrypy.request.method
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rcode = {'err': err}
        except Exception:
            err = 'Exception on BetterAnalyzeResouce.index: %s' % sys.exc_info()[
                1]
            cherrypy.response.status = 500
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
            rcode = {'err': err}

        return rcode
