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
import jobsub 
from auth import check_auth
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
    def index(self, acctgroup, setprio=None,
              param=None, paramval=None, **kwargs):
        """index.html for above URL
        parameters:
            @acctgroup: condor accounting group derived from <group_id> in URL
            @setprio : value to set condor priority to
            @param: currently must be 'job_id' to signal pathway to condor_prio
            @paramval: <jobsubjobid> that is having its priority set to '<prio>'
        """
        #logger.log('setprio=%s param=%s paramval=%s kwargs=%s' %
        #           (setprio, param, paramval, kwargs))
        user = None
        job_id = None
        err = '' 
        out = ''
        rval = {'out': out, 'err': err}
        rval['status']='starting'
        rval['setprio']=setprio
        rval['param']=param
        rval['paramval']=paramval
        rval['kwargs']=kwargs
        if jobsub.log_verbose():
            logger.log(rval)
        if setprio and not kwargs.get('prio'):
            kwargs['prio'] = setprio

        try:
            if param and paramval:
                if param == 'job_id':
                    job_id = paramval

                else:
                    err = "must supply a job_id"
                    rval['err']=err
                    rval['status']='error'
                    logger.log(rval)

            if not rval['err']:
                if jobsub.is_supported_accountinggroup(acctgroup):
                    if cherrypy.request.method == 'PUT':
                        # hold/release/adjust
                        r_code = util.doPUT(acctgroup, user=user,
                                                  job_id=job_id, **kwargs)

                        rval['status'] = 'returning from util.doPUT'
                        if r_code.get('out'):
                            rval['out'] = r_code['out']
                        if r_code.get('err'):
                            rval['err'] = r_code['err']
                        logger.log(rval)
                    else:
                        rval['status']='error'
                        rval['err'] = 'Unsupported method: %s' % cherrypy.request.method
                        logger.log(rval, severity=logging.ERROR)
                        logger.log(rval, severity=logging.ERROR, logfile='error')
                else:
                    # return error for unsupported acctgroup
                    rval['err'] = 'AccountingGroup %s is not configured in jobsub' %\
                            acctgroup
                    rval['status']='error'
                    logger.log(rval, severity=logging.ERROR)
                    logger.log(rval, severity=logging.ERROR, logfile='error')
        except BaseException as bae:
            cherrypy.response.status = 500
            rval['err'] = str(bae)
            rval['status']='error'
            logger.log(rval, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
        if rval.get('err'):
            cherrypy.response.status = 500
            rval['status'] = 'exit_error'
        else:
            rval['status']='exit_success'
        if jobsub.log_verbose():
            logger.log(rval)
        return rval

    def default(self, **kwargs):
        """Try to catch and log anything that ends up here by mistake
        """
        logger.log("kwargs %s" % kwargs)
