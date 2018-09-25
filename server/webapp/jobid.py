"""Module:
        jobid
   Purpose:
        query jobs by jobid from url /jobsub/jobs/jobid/<jobid>
   Author:
        Dennis Box
"""
import cherrypy
import logger
import logging

from format import format_response
from condor_commands import ui_condor_q
from condor_commands import constructFilter
from queued_outformat import QueuedFormattedOutputResource
from queued_jobstatus import QueuedJobStatusResource
from better_analyze import BetterAnalyzeResource
from request_headers import get_client_dn


@cherrypy.popargs('job_id')
class QueuedJobsByJobIDResource(object):
    """ Query list of job_ids. Returns a JSON list object.
     API is /jobsub/jobs/jobid/<jobid>
     """

    def __init__(self):
        """constructor
        """
        qfr = QueuedFormattedOutputResource()
        self.long = qfr
        self.dags = qfr
        qjs = QueuedJobStatusResource()
        self.hold = qjs
        self.run = qjs
        self.idle = qjs
        self.betteranalyze = BetterAnalyzeResource()

    def doGET(self, job_id, kwargs):
        """ perform http GET
        """
        my_filter = constructFilter(None, None, job_id)
        logger.log("my_filter=%s" % my_filter)
        queued_jobs = ui_condor_q(my_filter)
        logger.log('ui_condor_q result: %s' % queued_jobs)
        return {'out': queued_jobs.split('\n')}

    @cherrypy.expose
    @format_response
    def index(self, job_id=None, **kwargs):
        """index.html
        """
        try:
            subject_dn = get_client_dn()
            logger.log("job_id %s" % job_id)
            logger.log("kwargs %s" % kwargs)
            if subject_dn is not None:

                logger.log('subject_dn: %s' % subject_dn)
                if cherrypy.request.method == 'GET':
                    rcode = self.doGET(job_id, kwargs)
                else:
                    err = 'Unsupported method: %s' % cherrypy.request.method
                    logger.log(err)
                    logger.log(err, severity=logging.ERROR)
                    logger.log(err, severity=logging.ERROR, logfile='error')
                    rcode = {'err': err}
            else:
                # return error for no subject_dn
                err = 'User has not supplied subject dn'
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rcode = {'err': err}
        except Exception:
            err = 'Exception on QueuedJobsByJobIDResource.index'
            cherrypy.response.status = 500
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
            rcode = {'err': err}

        return rcode
