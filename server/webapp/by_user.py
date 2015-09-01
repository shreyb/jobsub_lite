import base64
import random
import os
import re
import cherrypy
import logger
import sys
import StringIO
from shutil import copyfileobj

from auth import check_auth, get_client_dn
from jobsub import is_supported_accountinggroup
from jobsub import condor_bin
from jobsub import run_cmd_as_user
from format import format_response
from condor_commands import condor, schedd_list



@cherrypy.popargs('action_user')
class AccountJobsByUserResource(object):
    def __init__(self):
        cherrypy.request.role = None
        cherrypy.request.username = None
        cherrypy.request.vomsProxy = None
        self.condorActions = {
            'REMOVE': condor.JobAction.Remove,
            'HOLD': condor.JobAction.Hold,
            'RELEASE': condor.JobAction.Release,
        }
        self.condorCommands = {
            'REMOVE': 'condor_rm',
            'HOLD': 'condor_hold',
            'RELEASE': 'condor_release',
        }




    def doDELETE(self, acctgroup,  user=None):
        rc = {'out': None, 'err': None}

        rc['out'] = self.doJobAction(
                            acctgroup,  user=user,
                            job_action='REMOVE')

        return rc


    def doPUT(self, acctgroup,  user=None,  **kwargs):
        """
        Executed to hold and release jobs
        """

        rc = {'out': None, 'err': None}
        job_action = kwargs.get('job_action')

        if job_action and job_action.upper() in self.condorCommands:
            rc['out'] = self.doJobAction(
                                acctgroup,  user=user,
                                job_action=job_action.upper())
        else:

            rc['err'] = '%s is not a valid action on jobs' % job_action

        logger.log(rc)

        return rc


   

    @cherrypy.expose
    @format_response
    def default(self,kwargs):
        logger.log('kwargs=%s'%kwargs)
        return {'out':"kwargs=%s"%kwargs}

    @cherrypy.expose
    @format_response
    @check_auth
    def index(self, acctgroup,  action_user=None, **kwargs):
        try:
            logger.log('action_user=%s'%(action_user))
            cherrypy.request.role = kwargs.get('role')
            cherrypy.request.username = kwargs.get('username')
            cherrypy.request.vomsProxy = kwargs.get('voms_proxy')
            if is_supported_accountinggroup(acctgroup):
                if cherrypy.request.method == 'DELETE':
                    #remove job
                    rc = self.doDELETE(acctgroup, user=action_user)
                elif cherrypy.request.method == 'PUT':
                    #hold/release
                    rc = self.doPUT(acctgroup,  user=action_user, **kwargs)
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


    def doJobAction(self, acctgroup, user=None, job_action=None):
        scheddList = []
        if user:
            constraint = '(Owner =?= "%s") && regexp("group_%s.*",AccountingGroup)' % (user,acctgroup)
            scheddList = schedd_list()

        reason = """jobsub_client command %s  %s""" % (get_client_dn(), cherrypy.request.headers.get('Remote-Addr'))
        logger.log("Performing %s -reason '%s' on jobs with constraints (%s)" % (job_action, reason, constraint))

                            
        child_env = os.environ.copy()
        child_env['X509_USER_PROXY'] = cherrypy.request.vomsProxy
        out = err = ''
        affected_jobs = 0
        regex = re.compile('^job_[0-9]+_[0-9]+[ ]*=[ ]*[0-9]+$')
        extra_err = ""
        for schedd_name in scheddList:
            try:
                cmd = [
                    condor_bin(self.condorCommands[job_action]), '-l',
                    '-name', schedd_name,
                    '-constraint', constraint,
                    '-reason', reason,
                ]
                out, err = run_cmd_as_user(cmd, cherrypy.request.username, child_env=child_env)
            except:
                #TODO: We need to change the underlying library to return
                #      stderr on failure rather than just raising exception
                #however, as we are iterating over schedds we don't want
                #to return error condition if one fails, we need to 
                #continue and process the other ones
                err="%s: exception:  %s "%(cmd,sys.exc_info()[1])
                logger.log(err,traceback=1)
                extra_err = extra_err + err
                #return {'out':out, 'err':err}
            out = StringIO.StringIO('%s\n' % out.rstrip('\n')).readlines()
            for line in out:
                if regex.match(line):
                    affected_jobs += 1
        retStr = "Performed %s on %s jobs matching your request %s" % (job_action, affected_jobs, extra_err)
        return retStr
