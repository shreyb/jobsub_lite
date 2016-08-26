import cherrypy
import logger
import logging

from format import format_response
from condor_commands import ui_condor_q, constructFilter
#from not_implemented import NotImplementedResource
from queued_long import QueuedLongResource
from queued_hold import QueuedHoldResource
from queued_dag import QueuedDagResource
from better_analyze import BetterAnalyzeResource
from auth import get_client_dn


@cherrypy.popargs('job_id')
class QueuedJobsByJobIDResource(object):

    def __init__(self):
        self.long = QueuedLongResource()
        self.hold = QueuedHoldResource('hold')
        self.run = QueuedHoldResource('run')
        self.idle = QueuedHoldResource('idle')
        self.dags = QueuedDagResource()
        self.betteranalyze = BetterAnalyzeResource()

    def doGET(self, job_id, kwargs):
        """ Query list of job_ids. Returns a JSON list object.
            API is /jobsub/jobs/jobid/<jobid>
        """
        filter = constructFilter(None, None, job_id)
        logger.log("filter=%s" % filter)
        queued_jobs = ui_condor_q(filter)
        logger.log('ui_condor_q result: %s' % queued_jobs)
        return {'out': queued_jobs.split('\n')}

    @cherrypy.expose
    @format_response
    def index(self, job_id=None, **kwargs):
        try:
            subject_dn = get_client_dn()
            logger.log("job_id %s" % job_id)
            logger.log("kwargs %s" % kwargs)
            if subject_dn is not None:

                logger.log('subject_dn: %s' % subject_dn)
                if cherrypy.request.method == 'GET':
                    rc = self.doGET(job_id, kwargs)
                else:
                    err = 'Unsupported method: %s' % cherrypy.request.method
                    logger.log(err)
                    logger.log(err, severity=logging.ERROR)
                    logger.log(err, severity=logging.ERROR, logfile='error')
                    rc = {'err': err}
            else:
                # return error for no subject_dn
                err = 'User has not supplied subject dn'
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rc = {'err': err}
        except:
            err = 'Exception on QueuedJobsByJobIDResource.index'
            cherrypy.response.status = 500
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
            rc = {'err': err}

        return rc
