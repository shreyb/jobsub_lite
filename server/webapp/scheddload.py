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
from JobsubConfigParser import JobsubConfigParser
from format import format_response


@cherrypy.popargs('acctgroup')
class ScheddLoadResource(object):

    def doGET(self, acctgroup, kwargs):

        jcp = JobsubConfigParser()

        #if 'ha_proxy_picks_schedd' in jobsub.ini, just return a 'dummy' answer
        #that the client will accept, it will get steered to proper server
        if jcp.get('default', 'ha_proxy_picks_schedd'):
            hostname = socket.gethostname()
            return {'out': ["%s  0" % hostname]}
        else:
            # return a list of schedds to client configurable by
            # schedd_load_metric, vo_constraint, and downtime_constraint
            # from jobsub.ini
            jobs = ui_condor_status_totalrunningjobs(acctgroup=acctgroup,
                                                     check_downtime=True)
            return {'out': jobs.split('\n')}

    @cherrypy.expose
    @format_response
    def index(self, acctgroup=None, **kwargs):
        logger.log('acctgroup=%s, kwargs=%s' % (acctgroup, kwargs))
        try:
            if cherrypy.request.method == 'GET':
                rc = self.doGET(acctgroup, kwargs)
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
