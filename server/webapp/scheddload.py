import cherrypy
import logger
import sys
import os
from condor_commands import ui_condor_status_totaljobs

from auth import check_auth
from format import format_response




class ScheddLoadResource(object):

    def doGET(self, kwargs):
	jobs = ui_condor_status_totaljobs()
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
            err = 'Exception on ScheddLoadResource.index: %s'%sys.exc_info()[1]
            cherrypy.response.status = 500
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc

