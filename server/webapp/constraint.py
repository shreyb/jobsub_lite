import base64
import random
import os
import re
import cherrypy
import logger
import sys
import util

from auth import check_auth, get_client_dn
from jobsub import is_supported_accountinggroup
from format import format_response
from condor_commands import ui_condor_q



@cherrypy.popargs('constraint')
class JobActionByConstraintResource(object):

    @cherrypy.expose
    @format_response
    @check_auth(pass_through='GET')
    def index(self, acctgroup,  constraint=None, **kwargs):
        try:
            cherrypy.request.role = kwargs.get('role')
            cherrypy.request.username = kwargs.get('username')
            cherrypy.request.vomsProxy = kwargs.get('voms_proxy')
            logger.log('constraint=%s'%(constraint))
            logger.log('kwargs=%s'%kwargs)
            if is_supported_accountinggroup(acctgroup):
                if cherrypy.request.method == 'DELETE':
                    #remove job
                    rc = util.doDELETE(acctgroup, constraint=constraint, **kwargs )
                elif cherrypy.request.method == 'PUT':
                    #hold/release
                    rc = util.doPUT(acctgroup,  constraint=constraint, **kwargs)
                elif cherrypy.request.method == 'GET':
                    #query
                    rc = self.doGET( constraint=constraint, **kwargs)
                else:
                    err = 'Unsupported method: %s' % cherrypy.request.method
                    logger.log(err)
                    rc = {'err': err}
            else:
                # return error for unsupported acctgroup
                err = 'AccountingGroup %s is not configured in jobsub' % acctgroup
                logger.log(err)
                rc = {'err': err}
        except:
            cherrypy.response.status = 500
            err = 'Exception on JobActionByConstraintResource.index'
            logger.log(err, traceback=True)
            rc = {'err': err}
        if rc.get('err'):
            cherrypy.response.status = 500
        return rc


    def doGET(self, constraint=None, **kwargs):
        """ Serves the following APIs:

        """
        logger.log('constraint=%s'%constraint)
        q_filter = "-constraint '%s'" % constraint
        q=ui_condor_q(q_filter)
        all_jobs=q.split('\n')
        if len(all_jobs)<1:
            logger.log('condor_q %s returned no jobs'% q_filter)
            err = 'condor_q %s returns no jobs' %  q_filter
            rc={'err':err}
        else:
            rc={'out':all_jobs}

        return rc


