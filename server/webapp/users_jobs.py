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
            err = 'Exception on UsersJobsResource.index: %s'%sys.exc_info()[1]
            cherrypy.response.status = 500
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc

    @cherrypy.expose
    @cherrypy.popargs('param1')
    @cherrypy.popargs('param2')
    @cherrypy.popargs('param3')
    @cherrypy.popargs('param4')
    @cherrypy.popargs('param5')
    @format_response
    def default(self,param1,param2=None,param3=None, param4=None, param5=None,  **kwargs):
        cherrypy.response.status = 501
	logger.log("param1 %s param2 %s param3 %s param4 %s param5 %s"%(param1, param2, param3, param4, param5))
        try:
            if cherrypy.request.method == 'GET':
                if param2=="jobs":
			if param3=='long' or param3=='dags':
				outFormat=param3
				param3=None
			elif param4=='long' or param4=='dags':
				outFormat=param4
			else:
				outFormat=None

        		cherrypy.response.status = 200 
        		filter = constructFilter(None,param1,param3)
        		logger.log("filter=%s"%filter)
        		user_jobs = ui_condor_q( filter, outFormat )
        		return {'out': user_jobs.split('\n')}

		else:
                	rc = {'out':'informational page for %s/%s/%s/%s/%s not implemented' % (param1,param2,param3,param4,param5)}
            else:
                err = 'Unimplemented method: %s' % cherrypy.request.method
                logger.log(err)
                rc = {'err': err}
        except:
            err = 'Exception on UsersJobsResource.default: %s'%sys.exc_info()[1]
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc
