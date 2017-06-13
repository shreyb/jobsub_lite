"""Module:
        constraint

   Purpose:
        implements query,hold,release, and remove jobs
        subject to condor_constraints

        API for hold,release,remove jobs:
        /jobsub/acctgroups/<get>/jobs/constraint/<constraint>
        /jobsub/acctgroups/<get>/jobs/constraint/<constraint>/<owner>

        API for query:
        /jobsub/acctgroups/<get>/jobs/constraint/<constraint>
        /jobsub/acctgroups/<get>/jobs/constraint/<constraint>/<output_format>
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
from condor_commands import ui_condor_q


@cherrypy.popargs('constraint', 'post_constraint')
class JobActionByConstraintResource(object):
    """Class implementing hold/release/remove/query by constraint

       http request method    condor action
       ------------------     -------------
       DELETE                 remove
       PUT                    hold/release
       GET                    query
    """

    @cherrypy.expose
    @format_response
    @check_auth(pass_through='GET')
    def index(self, acctgroup, constraint=None, **kwargs):
        try:
            if kwargs.get('role'):
                cherrypy.request.role = kwargs.get('role')
            if kwargs.get('username'):
                cherrypy.request.username = kwargs.get('username')
            if kwargs.get('voms_proxy'):
                cherrypy.request.vomsProxy = kwargs.get('voms_proxy')
            logger.log('constraint=%s' % (constraint))
            logger.log('kwargs=%s' % kwargs)
            if is_supported_accountinggroup(acctgroup):
                if cherrypy.request.method == 'DELETE':
                    # remove job
                    rcode = util.doDELETE(acctgroup,
                                          constraint=constraint,
                                          user=kwargs.get('post_constraint'),
                                          **kwargs)
                elif cherrypy.request.method == 'PUT':
                    # hold/release
                    rcode = util.doPUT(acctgroup, constraint=constraint,
                                       user=kwargs.get('post_constraint'),
                                       **kwargs)
                elif cherrypy.request.method == 'GET':
                    # query
                    rcode = self.doGET(constraint=constraint, **kwargs)
                else:
                    err = 'Unsupported method: %s' % cherrypy.request.method
                    logger.log(err, severity=logging.ERROR)
                    logger.log(err, severity=logging.ERROR, logfile='error')
                    rcode = {'err': err}
            else:
                # return error for unsupported acctgroup
                err = 'AccountingGroup %s is not configured in jobsub' % \
                    acctgroup
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rcode = {'err': err}
        except:
            cherrypy.response.status = 500
            err = 'Exception on JobActionByConstraintResource.index'
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
            rcode = {'err': err}
        #if rcode.get('err'):
        #    cherrypy.response.status = 500
        return rcode

    def doGET(self, constraint=None, **kwargs):
        """ Serves the following APIs:
            /jobsub/acctgroups/<grp>/jobs/constraint/<constraint>
            /jobsub/acctgroups/<grp>/jobs/constraint/<constraint>/<ouputformat>

        """
        logger.log('constraint=%s' % constraint)
        q_filter = "-constraint '%s'" % constraint
        fmt = kwargs.get('post_constraint')
        qry = ui_condor_q(q_filter, fmt)
        all_jobs = qry.split('\n')
        if len(all_jobs) < 1:
            logger.log('condor_q %s returned no jobs' % q_filter)
            err = 'condor_q %s returns no jobs' % q_filter
            rcode = {'err': err}
        else:
            rcode = {'out': all_jobs}

        return rcode
