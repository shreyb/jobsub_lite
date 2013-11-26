import cherrypy
import logger

from job import JobsResource
from auth import check_auth
from format import format_response
from jobsub import is_supported_accountinggroup


@cherrypy.popargs('acctgroup')
class AccountingGroupsResource(object):
    def __init__(self):
        self.jobs = JobsResource()

    def doGET(self, acctgroup):
        return {'out': acctgroup}

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
                if check_auth(subject_dn, acctgroup):
                    if acctgroup is not None:
                        logger.log('acctgroup: %s' % acctgroup)
                        if is_supported_accountinggroup(acctgroup):
                            if cherrypy.request.method == 'GET':
                                rc = self.doGET(acctgroup)
                        else:
                            # return error for unsupported acctgroup
                            err = 'AccountingGroup %s is not configured in jobsub' % acctgroup
                            logger.log(err)
                            rc = {'err': err}
                    else:
                        # return error for no acctgroup
                        err = 'User has not supplied acctgroup'
                        logger.log(err)
                        rc = {'err': err}
                else:
                    # return error for failed auth
                    err = 'User authorization has failed'
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

        return format_response(content_type_accept, rc)
