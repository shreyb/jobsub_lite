import cherrypy
import logger

from auth import check_auth, get_client_dn
from format import format_response
from sqlite_commands import jobsub_history,constructQuery




@cherrypy.popargs('user_id','job_id')
class HistoryResource(object):

    def doGET(self, user_id=None,job_id=None,**kwargs):
        """ Query list of user_ids. Returns a JSON list object.
	    API is /acctgroups/<group>/users/<user_id>jobs/history
        """
        acctgroup=kwargs.get('acctgroup')
        if job_id is None:
            job_id=kwargs.get('job_id')
        if user_id is None:
            user_id = kwargs.get('user_id')
        filter = constructQuery(acctgroup,user_id,job_id)
        logger.log("filter=%s"%filter)
	history = jobsub_history( filter  )
        return {'out': history}

    @cherrypy.expose
    @format_response
    def index(self, user_id=None, job_id=None, **kwargs):
        try:
            subject_dn = get_client_dn()
            logger.log("user_id %s"%user_id)
            logger.log("job_id %s"%job_id)
            logger.log("kwargs %s"%kwargs)
            if subject_dn is not None:

                logger.log('subject_dn: %s' % subject_dn)
                if cherrypy.request.method == 'GET':
                    logger.log('user_id=%s job_id=%s'%(user_id,job_id))
                    rc = self.doGET(user_id,job_id,**kwargs)
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
            err = 'Exception on HistoryResouce.index'
            cherrypy.response.status = 500
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc
