import cherrypy
import logger
import sys

from condor_commands import ui_condor_q, constructFilter
from format import format_response




class QueuedHoldResource(object):
    def __init__(self,jobstatus='hold'):
        cherrypy.response.status = 501
        self.jobstatus = jobstatus 
        #logger.log('jobstatus=%s'%self.jobstatus)

    def doGET(self, kwargs):
        #logger.log('kwargs=%s'%kwargs)
        #logger.log('id=%s status=%s'%(self,self.jobstatus))
        cherrypy.response.status = 200
        acctgroup=kwargs.get('acctgroup',None)
        user_id=kwargs.get('user',None)
        job_id=kwargs.get('job_id',None)
        my_filter = constructFilter(acctgroup, user_id, job_id, jobstatus=self.jobstatus )
        logger.log("filter=%s status=%s" % (my_filter, self.jobstatus))
        user_jobs = ui_condor_q( my_filter, self.jobstatus )
        return {'out': user_jobs.split('\n')}


    @cherrypy.expose
    @format_response
    def index(self,  **kwargs):
        cherrypy.response.status = 501
        try:
            if cherrypy.request.method == 'GET':
                rc = self.doGET(kwargs)
            else:
                err = 'Unimplemented method: %s' % cherrypy.request.method
                logger.log(err)
                rc = {'err': err}
        except:
            err = 'Exception on QueuedHoldResouce.index: %s'%sys.exc_info()[1]
            cherrypy.response.status = 500
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc

