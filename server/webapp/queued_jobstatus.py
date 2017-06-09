"""
 Description:
   This module implements jobsub_q --hold, --run, --idle

 Project:
   JobSub

 Author:
   Dennis Box

 TODO:
   the constructor has an unnecessary parameter which is
   ignored, take it out

"""
import cherrypy
import logger
import logging
import sys
import request_headers

from condor_commands import ui_condor_q, constructFilter
from format import format_response


class QueuedJobStatusResource(object):

    def __init__(self, jobstatus='hold'):
        cherrypy.response.status = 501
        self.jobstatus = jobstatus
        # logger.log('jobstatus=%s'%self.jobstatus)

    def doGET(self, jobstatus, kwargs):
        #logger.log('kwargs=%s' % kwargs)
        #logger.log('status=%s' % (jobstatus))
        cherrypy.response.status = 200
        acctgroup = kwargs.get('acctgroup', None)
        user_id = kwargs.get('user', None)
        job_id = kwargs.get('job_id', None)
        my_filter = constructFilter(acctgroup,
                                    user_id, job_id,
                                    jobstatus=jobstatus)
        #logger.log("filter=%s status=%s" % (my_filter, jobstatus))
        user_jobs = ui_condor_q(my_filter,jobstatus)
        return {'out': user_jobs.split('\n')}

    @cherrypy.expose
    @format_response(output_format='pre')
    def index(self, **kwargs):
        cherrypy.response.status = 501
        logger.log('kwargs=%s ' % (kwargs))
        jobstatus = request_headers.path_end()
        try:
            if cherrypy.request.method == 'GET':
                rc = self.doGET(jobstatus, kwargs)
            else:
                err = 'Unimplemented method: %s' % cherrypy.request.method
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rc = {'err': err}
        except:
            err = 'Exception on QueuedHoldResouce.index: %s' % sys.exc_info()[
                1]
            cherrypy.response.status = 500
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err,
                       severity=logging.ERROR,
                       logfile='error',
                       traceback=True)
            rc = {'err': err}

        return rc
