"""
 Description:
   This module helps to implement primitive load balancing
   by returning a list of running schedds and the total
   number of running jobs per schedd


 Project:
   JobSub

 Author:
   Dennis Box

"""
import cherrypy
import logger
import logging
import sys
from condor_commands import ui_condor_status_totalrunningjobs
import socket
import os

from format import format_response


@cherrypy.popargs('acctgroup')
class ScheddLoadResource(object):

    def doGET(self, acctgroup, kwargs):
        """
        perform http GET
        """

        if os.environ.get('JOBSUB_TURN_OFF_SCHEDD_BALANCE'):
            hostname = socket.gethostname()
            return {'out': ["%s  0" % hostname]}
        else:
            jobs = ui_condor_status_totalrunningjobs(acctgroup=acctgroup,
                                                     check_downtime=True)
            return {'out': jobs.split('\n')}

    @cherrypy.expose
    @format_response
    def index(self, acctgroup=None, **kwargs):
        """
        index.html for jobsub/scheddload
        """

        logger.log('acctgroup=%s, kwargs=%s' % (acctgroup, kwargs))
        try:
            if cherrypy.request.method == 'GET':
                ret_code = self.doGET(acctgroup, kwargs)
            else:
                err = 'Unimplemented method: %s' % cherrypy.request.method
                logger.log(err)
                logger.log(err, severity=logging.ERROR, logfile='error')
                ret_code = {'err': err}
        except Exception:
            err = 'Exception on ScheddLoadResource.index: %s' % sys.exc_info()[
                1]
            cherrypy.response.status = 500
            logger.log(err, traceback=True)
            logger.log(err,
                       traceback=True,
                       severity=logging.ERROR,
                       logfile='error')
            ret_code = {'err': err}

        return ret_code
