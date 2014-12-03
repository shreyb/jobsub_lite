import cherrypy
import logger

from auth import check_auth
from format import format_response
from condor_commands import ui_condor_q, constructFilter
#from history import HistoryResource
from queued_jobs import QueuedJobsResource




@cherrypy.popargs('user_id')
class UsersResource(object):
    def __init__(self):
        self.jobs=QueuedJobsResource()

    def doGET(self, user_id,kwargs):
        """ Query list of user_ids. Returns a JSON list object.
	    API is /acctgroups/<group>/users
	    API is /acctgroups/<group>/users/<user_id>
	    API is /acctgroups/<group>/users/<user_id>?job_id=<number>
        """
        acctgroup=kwargs.get('acctgroup')
        job_id=kwargs.get('job_id')
        filter = constructFilter(acctgroup,user_id,job_id)
        logger.log("filter=%s"%filter)
	all_jobs = ui_condor_q( filter  )
        return {'out': all_jobs.split("\n")}

    @cherrypy.expose
    @format_response
    def index(self, user_id=None, **kwargs):
        try:
            subject_dn = cherrypy.request.headers.get('Auth-User')
            logger.log("user_id %s"%user_id)
            logger.log("kwargs %s"%kwargs)
            if subject_dn is not None:

                logger.log('subject_dn: %s' % subject_dn)
                if cherrypy.request.method == 'GET':
                    rc = self.doGET(user_id,kwargs)
                else:
                    err = 'Unsupported method: %s' % cherrypy.request.method
                    logger.log(err)
                    rc = {'err': err}
            else:
                # return error for no subject_dn
                err = 'User has not supplied subject dn'
                logger.log(err)
                rc = {'err': err}
        except:
            err = 'Exception on UsersResource.index'
            cherrypy.response.status = 500
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc
