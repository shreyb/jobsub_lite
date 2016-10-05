"""
 Description:
   This module helps to implement primitive load balancing
   by returning a list of running schedds and the total
   number of running jobs per schedd


 Project:
   JobSub

 Author:
   Dennis Box

 TODO:
   The load balancing only looks at running jobs, it could do much
   better.
   It should be configurable from jobsub.ini or somewhere else
"""
import cherrypy
import logger
import logging
import sys
from condor_commands import ui_condor_status_totalrunningjobs

from format import format_response


class ScheddLoadResource(object):

    def doGET(self, kwargs):
        jobs = ui_condor_status_totalrunningjobs()
        return {'out': jobs.split('\n')}

    @cherrypy.expose
    @format_response
    def index(self, **kwargs):
        try:
            if cherrypy.request.method == 'GET':
                rc = self.doGET(kwargs)
            else:
                err = 'Unimplemented method: %s' % cherrypy.request.method
                logger.log(err)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rc = {'err': err}
        except:
            err = 'Exception on ScheddLoadResource.index: %s' % sys.exc_info()[
                1]
            cherrypy.response.status = 500
            logger.log(err, traceback=True)
            logger.log(err,
                       traceback=True,
                       severity=logging.ERROR,
                       logfile='error')
            rc = {'err': err}

        return rc
