import base64
import random
import os
import re
import cherrypy
import logger
import sys
import util
from shutil import copyfileobj

from auth import check_auth
from jobsub import is_supported_accountinggroup
from format import format_response



@cherrypy.popargs('job_id')
class RemoveForcexByJobIDResource(object):

    @cherrypy.expose
    @format_response
    @check_auth
    def index(self, acctgroup,  job_id=None, **kwargs):
        cherrypy.request.role = kwargs.get('role')
        cherrypy.request.username = kwargs.get('username')
        cherrypy.request.vomsProxy = kwargs.get('voms_proxy')

        try:
            logger.log('job_id=%s'%(job_id))
            kwargs['forcex'] = True
            logger.log('kwargs=%s'%kwargs)
            if is_supported_accountinggroup(acctgroup):
                if cherrypy.request.method == 'DELETE':
                    #remove job
                    rc = util.doDELETE(acctgroup, job_id=job_id, **kwargs )
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
            err = 'Exception on RemoveForcexByJobIDResource.index'
            logger.log(err, traceback=True)
            rc = {'err': err}
        if rc.get('err'):
            cherrypy.response.status = 500
        return rc


