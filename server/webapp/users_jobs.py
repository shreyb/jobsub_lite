import cherrypy
import logger
import sys

from format import format_response
from condor_commands import ui_condor_q, constructFilter




class UsersJobsResource(object):
    def __init__(self):
        cherrypy.response.status = 501

    def doGET(self, kwargs):
        return {'out': 'this url is not yet implemented'}

    @cherrypy.expose
    @format_response(output_format='pre')
    def index(self, **kwargs):
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
    @cherrypy.popargs('param6')
    @format_response(output_format='pre')
    def default(self, param1, param2=None, param3=None, param4=None, param5=None, param6=None, **kwargs):
        """ supports the following URLS
            users/<user>/jobs/
            users/<user>/jobs/long/
            users/<user>/jobs/dags/
            users/<user>/jobs/<jobid>
            users/<user>/jobs/<jobid>/dags/
            users/<user>/jobs/<jobid>/long/
            users/<user>/jobs/<jobid>/hold/
            users/<user>/jobs/acctgroup/<group>/
            users/<user>/jobs/acctgroup/<group>/dags/
            users/<user>/jobs/acctgroup/<group>/hold/
            users/<user>/jobs/<jobid>/acctgroup/<group>/
            users/<user>/jobs/<jobid>/acctgroup/<group>/dags/
            users/<user>/jobs/<jobid>/acctgroup/<group>/hold/
        """
        cherrypy.request.username = kwargs.get('username')
        cherrypy.response.status = 501
        logger.log("param1 %s param2 %s param3 %s param4 %s param5 %s param6 %s"%(param1, param2, param3, param4, param5, param6))
        try:
            if cherrypy.request.method == 'GET':
                if param2 == "jobs":
                    user = param1
                    jobid = None
                    acctgroup = None
                    fmt = None
                    nextIsAcctGroup = False
                    jobStatus = None

                    for p in [ param3, param4, param5, param6 ]:
                        if p in ['long','dags','hold','run','idle']:
                            fmt = p
                            if p in [ 'hold','run','idle']:
                                jobStatus = p
                        elif p in ['acctgroup']:
                            nextIsAcctGroup = True
                        elif nextIsAcctGroup:
                            acctgroup = p
                            nextIsAcctGroup = False
                        elif p is not None:
                            jobid = p
                        else:
                            break
                        

                    cherrypy.response.status = 200 
                    filter = constructFilter(acctgroup, user, jobid, jobStatus)
                    logger.log("filter=%s"%filter)
                    user_jobs = ui_condor_q(filter, fmt)
                    return {'out': user_jobs.split('\n')}

                else:
                    rc = {'out':'informational page for %s/%s/%s/%s/%s/%s not implemented' % (param1, param2, param3, param4, param5, param6)}
            else:
                err = 'Unimplemented method: %s' % cherrypy.request.method
                logger.log(err)
                rc = {'err': err}
        except:
            err = 'Exception on UsersJobsResource.default: %s'%sys.exc_info()[1]
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc
