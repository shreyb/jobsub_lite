"""
 Description:
   This module implements jobsub_q --summary

 Project:
   JobSub

 Author:
   Dennis Box

"""
import cherrypy
import logger
import logging
import sys
from condor_commands import ui_condor_queued_jobs_summary

from format import format_response


class JobSummaryResource(object):

    def doGET(self, kwargs):
        jobs = ui_condor_queued_jobs_summary()
        return {'out': jobs.split('\n')}

    @cherrypy.expose
    @format_response
    def index(self, **kwargs):
        try:
            if cherrypy.request.method == 'GET':
                rc = self.doGET(kwargs)
            else:
                err = 'Unimplemented method: %s' %\
                    cherrypy.request.method
                logger.log(err)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rc = {'err': err}
        except Exception:
            err = 'Exception on JobSummaryResouce.index: %s' % sys.exc_info()[
                1]
            cherrypy.response.status = 500
            logger.log(err, traceback=True)
            logger.log(err,
                       severity=logging.ERROR,
                       logfile='error',
                       traceback=True)
            rc = {'err': err}

        return rc
