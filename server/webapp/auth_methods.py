import cherrypy
import logger
import jobsub
from format import format_response




@cherrypy.popargs('auth_method')
class AuthMethodsResource(object):

    def doGET(self, auth_method,kwargs):
        """ Query list of auth_methods. Returns a JSON list object.
	    API is /acctgroups/<group>/authmethods/
	    API is /acctgroups/<group>/authmethods/<method_name>/
        """
        acctgroup=kwargs.get('acctgroup')
        logger.log('acctgroup=%s'%acctgroup)
        methods = jobsub.get_authentication_methods(acctgroup)
        if not auth_method:
            return {'out': methods}
        elif auth_method in methods:
            return {'out': '%s is valid for %s' % (auth_method,acctgroup) }
        else:
            cherrypy.response.status = 404
            return {'err': '%s is NOT found for %s' % (auth_method,acctgroup) }

    @cherrypy.expose
    @format_response
    def index(self, auth_method=None, **kwargs):
        try:
            logger.log("auth_method %s"%auth_method)
            logger.log("kwargs %s"%kwargs)

            if cherrypy.request.method == 'GET':
                rc = self.doGET(auth_method,kwargs)
            else:
                err = 'Unsupported method: %s' % cherrypy.request.method
                logger.log(err)
                rc = {'err': err}
        except:
            err = 'Exception on AuthMethodsResource.index'
            cherrypy.response.status = 500
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc