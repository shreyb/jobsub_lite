import cherrypy
import logger
import uuid
import os
import sys
import socket

from format import rel_link
from auth import check_auth, get_client_dn
from job import AccountJobsResource
from format import format_response
from jobsub import get_supported_accountinggroups
from jobsub import get_dropbox_path_root
from util import mkdir_p, digest_for_file, get_uid
from users import UsersResource
from dropbox import DropboxResource
from jobsub_help import JobsubHelpResource
from sandboxes import SandboxesResource
from configured_sites import ConfiguredSitesResource

from cherrypy.lib.static import serve_file

from shutil import copyfileobj, rmtree


@cherrypy.popargs('acctgroup')
class AccountingGroupsResource(object):
    def __init__(self):
        self.jobs = AccountJobsResource()
        self.users = UsersResource()
        self.help = JobsubHelpResource()
        self.dropbox = DropboxResource()
        self.sandboxes = SandboxesResource()
	self.sites=ConfiguredSitesResource()

    def doGET(self, acctgroup):
        """ Query list of accounting groups. Returns a JSON list object.
            API is /jobsub/acctgroups/
        """
        if acctgroup is None:
            out=[]
            for grp in get_supported_accountinggroups():
                out.append(rel_link(grp))
            return {'out': out}
        else:
            out = ['Accounting group %s'%acctgroup,['<a href=jobs/>running jobs</a>','<a href=sandboxes/>sandboxes for completed jobs</a>']]

            rc = {'out':out}
            return rc

    @cherrypy.expose
    @format_response
    def index(self, acctgroup=None, **kwargs):
        try:
            subject_dn = get_client_dn()
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
            err = 'Exception on AccountingGroupsResource.index: %s'% sys.exc_info()[1]
            cherrypy.response.status = 500
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc
