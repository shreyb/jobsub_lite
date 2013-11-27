import cherrypy
import logger

from job import AccountJobsResource
from format import format_response
from jobsub import get_supported_accountinggroups

@cherrypy.popargs('acctgroup')
class AccountingGroupsResource(object):
    def __init__(self):
        self.jobs = AccountJobsResource()

    def doGET(self, acctgroup):
        if acctgroup is None:
            return {'out': get_supported_accountinggroups()}
        else:
            # No action at this time
            pass

    @cherrypy.expose
    @format_response
    def index(self, acctgroup=None, **kwargs):
        try:
            subject_dn = cherrypy.request.headers.get('Auth-User')
            if subject_dn is not None:
                logger.log('subject_dn: %s' % subject_dn)
                if cherrypy.request.method == 'GET':
                    rc = self.doGET(acctgroup)
                else:
                    err = 'Unsupported method: %s' % cherrypy.request.method
                    logger.log(err)
                    rc = {'err': err}
            else:
                # return error for no subject_dn
                err = 'User has not supplied subject dn'
                logger.log(err)
                rc = {'err': err}
        except:
            err = 'Exception on JobsResouce.index'
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc
