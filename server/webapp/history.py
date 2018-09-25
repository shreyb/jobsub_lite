"""
 Description:
   This module implements server portion of jobsub_history commands
   it used to perform condor_history, but that was very slow and
   now it queries an SQLite database

 Project:
   JobSub

 Author:
   Dennis Box
"""
import cherrypy
import logger
import logging

from request_headers import get_client_dn
from format import format_response
from sqlite_commands import jobsub_history, constructQuery
import sys


@cherrypy.popargs('user_id', 'job_id')
class HistoryResource(object):

    def doGET(self, user_id=None, job_id=None, **kwargs):
        """ Query list of user_ids. Returns a JSON list object.
        API is /acctgroups/<group>/users/<user_id>jobs/history
        """
        try:
            acctgroup = kwargs.get('acctgroup')
            if job_id is None:
                job_id = kwargs.get('job_id')
            if user_id is None:
                user_id = kwargs.get('user_id')
            filter = constructQuery(acctgroup, user_id, job_id)
            logger.log("filter=%s" % filter)
            history = jobsub_history(filter)
            return {'out': history}
        except Exception:
            err = ' %s' % sys.exc_info()[1]
            cherrypy.response.status = 500
            logger.log(err, severity=logging.ERROR)
            logger.log(err, severity=logging.ERROR, logfile='error')
            return {'err': err}

    @cherrypy.expose
    @format_response
    def index(self, user_id=None, job_id=None, **kwargs):
        try:
            subject_dn = get_client_dn()
            logger.log("user_id %s" % user_id)
            logger.log("job_id %s" % job_id)
            logger.log("kwargs %s" % kwargs)
            if subject_dn is not None:

                logger.log('subject_dn: %s' % subject_dn)
                if cherrypy.request.method == 'GET':
                    logger.log('user_id=%s job_id=%s' % (user_id, job_id))
                    rc = self.doGET(user_id, job_id, **kwargs)
                else:
                    err = 'Unsupported method: %s' % cherrypy.request.method
                    logger.log(err, severity=logging.ERROR)
                    logger.log(err, severity=logging.ERROR, logfile='error')
                    rc = {'err': err}
            else:
                # return error for no subject_dn
                err = 'User has not supplied subject dn'
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rc = {'err': err}
        except Exception:
            err = 'Exception on HistoryResouce.index'
            cherrypy.response.status = 500
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
            rc = {'err': err}

        return rc

    @cherrypy.expose
    @cherrypy.popargs('param1')
    @cherrypy.popargs('param2')
    @cherrypy.popargs('param3')
    @cherrypy.popargs('param4')
    @cherrypy.popargs('param5')
    @cherrypy.popargs('param6')
    @cherrypy.popargs('param7')
    @cherrypy.popargs('param8')
    @cherrypy.popargs('param9')
    @cherrypy.popargs('param10')
    @cherrypy.popargs('param11')
    @cherrypy.popargs('param12')
    @format_response
    def default(self, param1, param2=None, param3=None, param4=None, param5=None, param6=None,
                pararm7=None, param8=None, param9=None, param10=None, param11=None, param12=None, **kwargs):
        """ supports the following URLS
        """
        try:
            params = [param1, param2, param3, param4, param5, param6,
                      pararm7, param8, param9, param10, param11, param12, ]
            logger.log("params %s " % (params))
            pDict = {}
            for n, i in enumerate(params):
                if i in ['user', 'acctgroup', 'jobid',
                         'qdate_ge', 'qdate_le', ]:
                    pDict[i] = params[n + 1]

            if pDict:
                filter = constructQuery(acctgroup=pDict.get('acctgroup'),
                                        uid=pDict.get('user'),
                                        jobid=pDict.get('jobid'),
                                        qdate_ge=pDict.get('qdate_ge'),
                                        qdate_le=pDict.get('qdate_le')
                                        )
                logger.log("filter=%s" % filter)
                history = jobsub_history(filter)
                return {'out': history}

            else:
                cherrypy.response.status = 501
                rc = {
                    'out': 'informational page for %s not implemented' % (params)}

        except Exception:
            err = 'Exception on HistoryResource.default: %s' % sys.exc_info()[
                1]
            cherrypy.response.status = 500
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
            rc = {'err': err}

        return rc
