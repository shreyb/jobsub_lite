"""
 Description:
   This module implements /jobsub/users/ and most of its sub leafs

 Project:
   JobSub

 Author:
   Dennis Box

"""
import cherrypy
import logger
import logging
import sys

from format import format_response, rel_link
#from condor_commands import ui_condor_q, constructFilter, condor_userprio
import condor_commands


class UsersJobsResource(object):
    """
    Only class in module, see module docstring
    """

    def __init__(self):
        cherrypy.response.status = 501

    def doGET(self, kwargs):
        """
        was the http request a GET? Go for it!
        """
        out2 = condor_commands.condor_userprio()
        users = ['Uids the batch system knows about:']

        for line in out2.split('\n'):
            if '@' in line:
                grps = line.split('@')
                uinfo = grps[0].split('.')
                uid_link = rel_link(uinfo[-1])
                if uid_link not in users:
                    users.append(uid_link)
        out = users
        out2 = "<pre>%s</pre>" % out2
        out.append(out2)
        return {'out': out}

    @cherrypy.expose
    @format_response
    def index(self, **kwargs):
        """
        index.html for /jobsub/users/
        """
        cherrypy.response.status = 501
        try:
            if cherrypy.request.method == 'GET':
                rc = self.doGET(kwargs)
            else:
                err = 'Unimplemented method: %s' % cherrypy.request.method
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rc = {'err': err}
        except Exception:
            err = 'Exception on UsersJobsResource.index: %s' % sys.exc_info()[
                1]
            cherrypy.response.status = 500
            logger.log(err, severity=logging.ERROR)
            logger.log(err, severity=logging.ERROR, logfile='error')
            rc = {'err': err}

        return rc

    @cherrypy.expose
    @cherrypy.popargs('param1')
    @cherrypy.popargs('param2')
    @cherrypy.popargs('param3')
    @cherrypy.popargs('param4')
    @cherrypy.popargs('param5')
    @cherrypy.popargs('param6')
    @format_response(output_format='pre')
    def default(self, param1, param2=None, param3=None, param4=None,
                param5=None, param6=None, **kwargs):
        """ supports the following URLS
            users/<user>/jobs/
            users/<user>/jobs/long/
            users/<user>/jobs/dags/
            users/<user>/jobs/<jobid>
            users/<user>/jobs/<jobid>/dags/
            users/<user>/jobs/<jobid>/long/
            users/<user>/jobs/<jobid>/hold/
            users/<user>/jobs/acctgroup/<group>/
            users/<user>/jobs/acctgroup/<group>/dags/
            users/<user>/jobs/acctgroup/<group>/hold/
            users/<user>/jobs/<jobid>/acctgroup/<group>/
            users/<user>/jobs/<jobid>/acctgroup/<group>/dags/
            users/<user>/jobs/<jobid>/acctgroup/<group>/hold/
        """
        if kwargs.get('username'):
            cherrypy.request.username = kwargs.get('username')
        cherrypy.response.status = 501
        logger.log(
            "param1 %s param2 %s param3 %s param4 %s param5 %s param6 %s" % (
                param1, param2, param3, param4, param5, param6))
        try:
            if cherrypy.request.method == 'GET':
                if param2 is None:
                    param2 = "jobs"
                if param2 == "jobs":
                    user = param1
                    jobid = None
                    acctgroup = None
                    fmt = None
                    nextIsAcctGroup = False
                    jobStatus = None

                    for p in [param3, param4, param5, param6]:
                        if nextIsAcctGroup and p is not None:
                            acctgroup = p
                            nextIsAcctGroup = False
                        elif p in ['long', 'dags', ]:
                            fmt = p
                        elif p in ['hold', 'run', 'idle', ]:
                            jobStatus = p
                        elif p in ['acctgroup']:
                            nextIsAcctGroup = True
                        elif p is not None:
                            jobid = p
                        else:
                            break

                    cherrypy.response.status = 200
                    q_filter = condor_commands.constructFilter(
                        acctgroup, user, jobid, jobStatus)
                    logger.log("q_filter=%s" % q_filter)
                    user_jobs = condor_commands.ui_condor_q(q_filter, fmt)
                    return {'out': user_jobs.split('\n')}

                else:
                    rc = {'out': 'informational page for %s/%s/%s/%s/%s/%s not implemented' % (
                        param1, param2, param3, param4, param5, param6)}
                    logger.log('%s' % rc)
            else:
                err = 'Unimplemented method: %s' % cherrypy.request.method
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rc = {'err': err}
        except Exception:
            err = 'Exception on UsersJobsResource.default: %s' % sys.exc_info()[
                1]
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
            rc = {'err': err}

        return rc
