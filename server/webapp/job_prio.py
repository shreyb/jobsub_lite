"""Module:
        by_user
   Purpose
        implements condor_q <username>
        API /jobsub/acctgroups/<group_id>/jobs/prio/<prio>/user/<username>
        API /jobsub/acctgroups/<group_id>/jobs/prio/<prio>job_id/<jobsubjobid>/
"""
import cherrypy
import logger
import logging
import util
from auth import check_auth
from jobsub import is_supported_accountinggroup
from format import format_response


@cherrypy.popargs('setprio','param','paramval')
class JobPrioResource(object):
    """Class that implements above URLS
       Only responds to http GET, only
       index.html implemented
    """

    @cherrypy.expose
    @format_response
    @check_auth
    def index(self, acctgroup,  setprio=None, param=None, paramval=None,**kwargs):
        logger.log('setprio=%s param=%s paramval=%s kwargs=%s' % (setprio,param,paramval,kwargs))
        user = None
        job_id = None
        err = None
        out = None
        rc = {'out': out, 'err': err}
        try:
            if param and paramval :
                if param =='job_id':
                    job_id=paramval

                if param =='user':
                    user=paramval
                kwargs['prio'] = setprio
                #kwargs['user'] = user
                #kwargs['job_id'] = job_id

            else:
                err = "must supply either a job_id or user"
                
            logger.log('user=%s job_id=%s' % (user, job_id))
            if is_supported_accountinggroup(acctgroup):
                if cherrypy.request.method == 'PUT':
                    # hold/release/adjust
                    rc = util.doPUT(acctgroup, user=user,
                               job_id=job_id, **kwargs)
                else:
                    err = 'Unsupported method: %s' % cherrypy.request.method
                    logger.log(err, severity=logging.ERROR)
                    logger.log(err, severity=logging.ERROR, logfile='error')
            else:
                # return error for unsupported acctgroup
                err = 'AccountingGroup %s is not configured in jobsub' % acctgroup
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
        except:
            cherrypy.response.status = 500
            err = 'Exception on AccountJobsByUserResource.index'
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
        if rc.get('err'):
            cherrypy.response.status = 500
        return rc
    
    def default(self,  **kwargs):
        logger.log("kwargs %s" % kwargs)
