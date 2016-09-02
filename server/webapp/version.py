import cherrypy
import logger
import sys
import os
import logging
from format import format_response


class VersionResource(object):

    def doGET(self, kwargs):
        tools_version = 'jobsub_tools now integrated into server'
        server_version = 'jobsub server rpm release: %s' %\
            os.environ.get('JOBSUB_SERVER_VERSION')
        if not server_version:
            server_version = 'Unknown'
        return {'out': [server_version, tools_version]}

    @cherrypy.expose
    @format_response
    def index(self, **kwargs):
        try:
            if cherrypy.request.method == 'GET':
                rc = self.doGET(kwargs)
            else:
                err = 'Unimplemented method: %s' % cherrypy.request.method
                logger.log(err)
                logger.log(err,
                           traceback=True,
                           severity=logging.ERROR,
                           logfile='error')
                rc = {'err': err}
        except:
            err = 'Exception on VersionResouce.index: %s' % sys.exc_info()[1]
            cherrypy.response.status = 500
            logger.log(err, traceback=True)
            logger.log(err,
                       traceback=True,
                       severity=logging.ERROR,
                       logfile='error')
            rc = {'err': err}

        return rc
