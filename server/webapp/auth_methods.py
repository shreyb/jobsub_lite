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
import json
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
        r_code={'status':'start','auth_method':auth_method, 'acctgroup':acctgroup, 'kwargs':kwargs}
        if jobsub.log_verbose():
            logger.log(json.dumps(r_code, sort_keys=True))
        methods = jobsub.get_authentication_methods(acctgroup)
        if not auth_method:
            r_code['out'] = methods
            r_code['status']='exiting'
            if jobsub.log_verbose():
                logger.log(json.dumps(r_code, sort_keys=True))
            return r_code
        elif auth_method in methods:
            stat = '%s is valid for %s' % (auth_method, acctgroup)
            r_code['out'] = stat
            r_code['status']='exiting'
            if jobsub.log_verbose():
                logger.log(json.dumps(r_code, sort_keys=True))
            return {'out': stat}
        else:
            cherrypy.response.status = 404
            stat = '%s is NOT found for %s' % (auth_method, acctgroup)
            r_code['err'] = stat
            r_code['status'] = 'exit_error'
            logger.log(json.dumps(r_code, sort_keys=True), severity=logging.ERROR)
            logger.log(json.dumps(r_code, sort_keys=True), severity=logging.ERROR, logfile='error')
            return r_code

    @cherrypy.expose
    @format_response
    def index(self, auth_method=None, **kwargs):
        """index.html, only GET implemented
        """
        try:
            if jobsub.log_verbose():
                logger.log("auth_method %s" % auth_method)
                logger.log("kwargs %s" % kwargs)

            if cherrypy.request.method == 'GET':
                rc = self.doGET(auth_method, kwargs)
            else:
                err = 'Unsupported method: %s' % cherrypy.request.method
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rc = {'err': err}
        except:
            err = 'Exception on AuthMethodsResource.index'
            cherrypy.response.status = 500
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
            rc = {'err': err}

        return rc
