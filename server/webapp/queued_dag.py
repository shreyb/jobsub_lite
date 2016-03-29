import cherrypy
import logger
import logging
import sys

from condor_commands import ui_condor_q, constructFilter
from format import format_response




class QueuedDagResource(object):
    def __init__(self):
        cherrypy.response.status = 501

    def doGET(self, kwargs):
        cherrypy.response.status = 200
	acctgroup = kwargs.get('acctgroup', None)
	user_id = kwargs.get('user', None)
	job_id = kwargs.get('job_id', None)
	filter = constructFilter(acctgroup, user_id, job_id)
	logger.log("filter=%s"%filter)
	user_jobs = ui_condor_q(filter, 'dags')
	return {'out': user_jobs.split('\n')}


    @cherrypy.expose
    @format_response(output_format='pre')
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
            err = 'Exception on QueuedDagResouce.index: %s'%sys.exc_info()[1]
            cherrypy.response.status = 500
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR, logfile='error', traceback=True)
            rc = {'err': err}

        return rc

