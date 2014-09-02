import cherrypy
import logger
import sys

from auth import check_auth
from format import format_response
from condor_commands import ui_condor_q,constructFilter
from queued_jobs import QueuedJobsResource




class UsersJobsResource(object):
    def __init__(self):
        cherrypy.response.status = 501

    def doGET(self, kwargs):
        return {'out': 'this url is not yet implemented'}

    @cherrypy.expose
    @format_response
    def index(self,  **kwargs):
        cherrypy.response.status = 501
        try:
            if cherrypy.request.method == 'GET':
                rc = self.doGET(kwargs)
            else:
                err = 'Unimplemented method: %s' % cherrypy.request.method
                logger.log(err)
                rc = {'err': err}
        except:
            err = 'Exception on NotImplementedResouce.index: %s'%sys.exc_info()[1]
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc

    @cherrypy.expose
    @cherrypy.popargs('param1')
    @cherrypy.popargs('param2')
    @format_response
    def default(self,param1,param2=None,param3=None,  **kwargs):
        cherrypy.response.status = 501
        try:
            if cherrypy.request.method == 'GET':
                if param2=="jobs":
        		cherrypy.response.status = 200 
        		filter = constructFilter(None,param1,None)
        		logger.log("filter=%s"%filter)
        		user_jobs = ui_condor_q( filter  )
        		return {'out': user_jobs.split('\n')}

		else:
                	rc = {'out':'informational page for %s/%s/%s not implemented' % (param1,param2,param3)}
            else:
                err = 'Unimplemented method: %s' % cherrypy.request.method
                logger.log(err)
                rc = {'err': err}
        except:
            err = 'Exception on NotImplementedResouce.default: %s'%sys.exc_info()[1]
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc
