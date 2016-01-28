import base64
import random
import os
import re
import cherrypy
import logger
import sys
import util
from shutil import copyfileobj

from auth import check_auth, get_client_dn
from jobsub import is_supported_accountinggroup
from format import format_response



@cherrypy.popargs('action_user','job_id')
class AccountJobsByUserResource(object):

    @cherrypy.expose
    @format_response
    @check_auth
    def index(self, acctgroup,  action_user=None, job_id=None, **kwargs):
        try:
            cherrypy.request.role = kwargs.get('role')
            cherrypy.request.username = kwargs.get('username')
            cherrypy.request.vomsProxy = kwargs.get('voms_proxy')
            logger.log('action_user=%s'%(action_user))
            logger.log('kwargs=%s'%kwargs)
            if is_supported_accountinggroup(acctgroup):
                if cherrypy.request.method == 'DELETE':
                    #remove job
                    rc = util.doDELETE(acctgroup, user=action_user, job_id=job_id,  **kwargs )
                elif cherrypy.request.method == 'PUT':
                    #hold/release
                    rc = util.doPUT(acctgroup,  user=action_user, job_id=job_id, **kwargs)
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
            err = 'Exception on AccountJobsByUserResource.index'
            logger.log(err, traceback=True)
            rc = {'err': err}
        if rc.get('err'):
            cherrypy.response.status = 500
        return rc

