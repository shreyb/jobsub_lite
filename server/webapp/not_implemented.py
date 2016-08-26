import cherrypy
import logger
import sys

from format import format_response




class NotImplementedResource(object):
    def __init__(self):
        cherrypy.response.status = 501

    def doGET(self, kwargs):
        return {'out': 'this url is not yet implemented %s %s'%(self.__class__.__name__,kwargs)}

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
    def default(self,param1,param2=None,param3=None,param4=None,param5=None,  **kwargs):
        cherrypy.response.status = 501
        try:
            if cherrypy.request.method == 'GET':
                rc = {'out':'informational page for %s/%s/%s/%s/%s not implemented %s %s' % (param1,param2,param3,param4,param5,self.__class__.__name__,kwargs)}
            else:
                err = 'Unimplemented method: %s' % cherrypy.request.method
                logger.log(err)
                rc = {'err': err}
        except:
            err = 'Exception on NotImplementedResouce.default: %s'%sys.exc_info()[1]
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc
