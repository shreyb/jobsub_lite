import cherrypy
import logger
import sys
import os
from condor_commands import ui_condor_queued_jobs_summary

from auth import check_auth
from format import format_response




class JobSummaryResource(object):

    def doGET(self, kwargs):
	jobs = ui_condor_queued_jobs_summary()
	return {'out':jobs.split('\n')}

    @cherrypy.expose
    @format_response
    def index(self,  **kwargs):
        try:
            if cherrypy.request.method == 'GET':
                rc = self.doGET(kwargs)
            else:
                err = 'Unimplemented method: %s' % cherrypy.request.method
                logger.log(err)
                rc = {'err': err}
        except:
            err = 'Exception on JobSummaryResouce.index: %s'%sys.exc_info()[1]
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc

