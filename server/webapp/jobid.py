import cherrypy
import logger

from format import format_response
from condor_commands import ui_condor_q,constructFilter




@cherrypy.popargs('job_id')
class QueuedJobsByJobIDResource(object):


    def doGET(self, job_id,kwargs):
        """ Query list of job_ids. Returns a JSON list object.
	    API is /jobsub/jobs/jobid/<jobid>
        """
        filter = constructFilter(None,None,job_id)
        logger.log("filter=%s"%filter)
	history = ui_condor_q( filter  )
        return {'out': history.split('\n')}

    @cherrypy.expose
    @format_response
    def index(self, job_id=None, **kwargs):
        try:
            subject_dn = cherrypy.request.headers.get('Auth-User')
            logger.log("job_id %s"%job_id)
            logger.log("kwargs %s"%kwargs)
            if subject_dn is not None:

                logger.log('subject_dn: %s' % subject_dn)
                if cherrypy.request.method == 'GET':
                    rc = self.doGET(job_id,kwargs)
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
            err = 'Exception on QueuedJobsByJobIDResource.index'
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc
