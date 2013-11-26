import cherrypy
import logger

from job import JobsResource
from format import format_response
from jobsub import get_supported_accountinggroups

@cherrypy.popargs('acctgroup')
class AccountingGroupsResource(object):
    def __init__(self):
        self.jobs = JobsResource()

    def doGET(self, acctgroup=None):
        if acctgroup is None:
            return {'out': get_supported_accountinggroups()}
        else:
            # No action at this time
            pass

    @cherrypy.expose
    # @format_response
    # @check_auth
    def index(self, acctgroup, **kwargs):
        content_type_accept = cherrypy.request.headers.get('Accept')
        logger.log('Request content_type_accept: %s' % content_type_accept)
        rc = dict()
        try:
            subject_dn = cherrypy.request.headers.get('Auth-User')
            if subject_dn is not None:
                logger.log('subject_dn: %s' % subject_dn)
                rc = self.doGET()
            else:
                # return error for no subject_dn
                err = 'User has not supplied subject dn'
                logger.log(err)
                rc = {'err': err}
        except:
            err = 'Exception on JobsResouce.index'
            logger.log(err, traceback=True)
            rc = {'err': err}

        return format_response(content_type_accept, rc)
