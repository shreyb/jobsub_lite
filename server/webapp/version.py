import cherrypy
import logger
import sys
import os

from auth import check_auth
from format import format_response




class VersionResource(object):

    def doGET(self, kwargs):
        version=os.environ.get('JOBSUB_SERVER_VERSION')
        if version is not None:
        	return {'out': 'Jobsub Server rpm release %s'%version}
        else:
		return {'out': "Version not set. Please contact jobsub-support@fnal.gov or open a service desk ticket"}

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
            err = 'Exception on VersionResouce.index: %s'%sys.exc_info()[1]
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc

