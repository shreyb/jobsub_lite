"""
 Description:
   Query supported authorization methods from jobsub.ini, returns a JSON
   list object.  Written for transition period of DCAFI project
   when groups transitioned to myproxy authentication on a group-by-group
   basis
   API is /acctgroups/<group>/authmethods/
   API is /acctgroups/<group>/authmethods/<method_name>/

 Project:
   JobSub

 Author:
   Dennis Box

"""
import cherrypy
import logger
import logging
import jobsub
from format import format_response


@cherrypy.popargs('auth_method')
class AuthMethodsResource(object):
    """see module documentation, only one class in file
    """

    def doGET(self, auth_method, kwargs):
        """ http GET request on index.html of API
            Query list of auth_methods. Returns a JSON list object.
            API is /acctgroups/<group>/authmethods/
            API is /acctgroups/<group>/authmethods/<method_name>/
        """
        acctgroup = kwargs.get('acctgroup')
        logger.log('acctgroup=%s' % acctgroup)
        methods = jobsub.get_authentication_methods(acctgroup)
        if not auth_method:
            return {'out': methods}
        elif auth_method in methods:
            return {'out': '%s is valid for %s' % (auth_method, acctgroup)}
        else:
            cherrypy.response.status = 404
            return {'err': '%s is NOT found for %s' % (auth_method, acctgroup)}

    @cherrypy.expose
    @format_response
    def index(self, auth_method=None, **kwargs):
        """index.html, only GET implemented
        """
        try:
            logger.log("auth_method %s" % auth_method)
            logger.log("kwargs %s" % kwargs)

            if cherrypy.request.method == 'GET':
                rc = self.doGET(auth_method, kwargs)
            else:
                err = 'Unsupported method: %s' % cherrypy.request.method
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rc = {'err': err}
        except Exception:
            err = 'Exception on AuthMethodsResource.index'
            cherrypy.response.status = 500
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
            rc = {'err': err}

        return rc
