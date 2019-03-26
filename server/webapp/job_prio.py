"""Module:
        job_prio
   Purpose
        sets up call to  condor_userprio -p <prio> <jobid>
        API /jobsub/acctgroups/<group_id>/jobs/setprio/<prio>job_id/<jobsubjobid>/
   Author 
        Dennis Box, dbox@fnal.gov
"""
import cherrypy
import logger
import logging
import util
from auth import check_auth
from jobsub import is_supported_accountinggroup
from format import format_response


@cherrypy.popargs('setprio', 'param', 'paramval')
class JobPrioResource(object):
    """Class that implements above URL
       and eventually calls condor_prio
       Only responds to http PUT
    """

    @cherrypy.expose
    @format_response
    @check_auth
    def index(self, acctgroup,  setprio=None, param=None, paramval=None, **kwargs):
        """index.html for above URL
        parameters:
            @acctgroup: condor accounting group derived from <group_id> in URL
            @setprio : value to set condor priority to
            @param: currently must be 'job_id' to signal pathway to condor_prio
            @paramval: <jobsubjobid> that is having its priority set to '<prio>'
        """
        logger.log('setprio=%s param=%s paramval=%s kwargs=%s' %
                   (setprio, param, paramval, kwargs))
        user = None
        job_id = None
        err = None
        out = None
        rc = {'out': out, 'err': err}
        try:
            if param and paramval:
                if param == 'job_id':
                    job_id = paramval

            else:
                err = "must supply a job_id"
                logger.log(rc)
            logger.log('user=%s job_id=%s' % (user, job_id))
            if is_supported_accountinggroup(acctgroup):
                if cherrypy.request.method == 'PUT':
                    # hold/release/adjust
                    rc = util.doPUT(acctgroup, user=user,
                                    job_id=job_id, **kwargs)
                else:
                    err = 'Unsupported method: %s' % cherrypy.request.method
                    logger.log(rc, severity=logging.ERROR)
                    logger.log(err, severity=logging.ERROR, logfile='error')
            else:
                # return error for unsupported acctgroup
                err = 'AccountingGroup %s is not configured in jobsub' % acctgroup
                logger.log(rc, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
        except:
            cherrypy.response.status = 500
            err = 'Exception on JobsPrioResource.index'
            logger.log(rc, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
        if rc.get('err'):
            cherrypy.response.status = 500
        return rc

    def default(self,  **kwargs):
        logger.log("kwargs %s" % kwargs)
