""" Module:
            forcex_jobid
    Purpose:
            condor_rm --forcex a single jobid
            API is  /jobsub/acctgroups/<acctgroup>/jobs/<job_id>/forcex
    Author:
            Dennis Box
"""
import cherrypy
import logger
import logging
import util

from auth import check_auth
from jobsub import is_supported_accountinggroup
from format import format_response


@cherrypy.popargs('job_id')
class RemoveForcexByJobIDResource(object):

    @cherrypy.expose
    @format_response
    @check_auth
    def index(self, acctgroup, job_id=None, **kwargs):
        if kwargs.get('role'):
            cherrypy.request.role = kwargs.get('role')
        if kwargs.get('username'):
            cherrypy.request.username = kwargs.get('username')
        if kwargs.get('voms_proxy'):
            cherrypy.request.vomsProxy = kwargs.get('voms_proxy')

        try:
            logger.log('job_id=%s' % (job_id))
            kwargs['forcex'] = True
            logger.log('kwargs=%s' % kwargs)
            if is_supported_accountinggroup(acctgroup):
                if cherrypy.request.method == 'DELETE':
                    # remove job
                    rcode = util.doDELETE(acctgroup, job_id=job_id, **kwargs)
                else:
                    err = 'Unsupported method: %s' % cherrypy.request.method
                    logger.log(err, severity=logging.ERROR)
                    logger.log(err, severity=logging.ERROR, logfile='error')
                    rcode = {'err': err}
            else:
                # return error for unsupported acctgroup
                err = 'AccountingGroup %s is not configured' % acctgroup
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rcode = {'err': err}
        except:
            cherrypy.response.status = 500
            err = 'Exception on RemoveForcexByJobIDResource.index'
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
            rcode = {'err': err}
        if rcode.get('err'):
            cherrypy.response.status = 500
        return rcode
