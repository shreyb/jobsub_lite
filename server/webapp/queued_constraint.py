import cherrypy
import logger
import logging
import sys

from condor_commands import ui_condor_q, constructFilter
from format import format_response


class QueuedConstraintResource(object):

    def __init__(self):
        cherrypy.response.status = 501

    def doGET(self, kwargs):
        cherrypy.response.status = 200
        acctgroup = kwargs.get('acctgroup', None)
        user_id = kwargs.get('user', None)
        job_id = kwargs.get('job_id', None)
        my_filter = constructFilter(
            acctgroup, user_id, job_id, jobstatus='hold')
        logger.log("filter=%s" % my_filter)
        user_jobs = ui_condor_q(my_filter, 'hold')
        return {'out': user_jobs.split('\n')}

    @cherrypy.expose
    @format_response
    def index(self, **kwargs):
        cherrypy.response.status = 501
        try:
            if cherrypy.request.method == 'GET':
                rc = self.doGET(kwargs)
            else:
                err = 'Unimplemented method: %s' % cherrypy.request.method
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rc = {'err': err}
        except:
            err = 'Exception on QueuedConstraintResouce.index: %s' % sys.exc_info()[
                1]
            cherrypy.response.status = 500
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
            rc = {'err': err}

        return rc
