"""Module:
    accounting_group
   Purpose:
    a central 'glue' and dispatch node when using
    cherrypy default dispatcher for Jobsub project
    API is /jobsub/acctgroups/<acctgroup>/
   Author:
    Nick Palombo
"""
import cherrypy
import logger
import logging
import sys

from format import rel_link
from request_headers import get_client_dn
from job import AccountJobsResource
from format import format_response
from jobsub import get_supported_accountinggroups
from users import UsersResource
from dropbox import DropboxResource
from jobsub_help import JobsubHelpResource
from sandboxes import SandboxesResource
from configured_sites import ConfiguredSitesResource
from auth_methods import AuthMethodsResource


@cherrypy.popargs('acctgroup')
class AccountingGroupsResource(object):
    """Implementation of
       API /jobsub/acctgroups/
       /jobsub/acctgroups/<acctgroup>/
       in constructor
            self.jobs is link to /jobsub/acctgroups/<acctgroup>/jobs/
            self.users goes to  /jobsub/acctgroups/<acctgroup>/users/
            etc
    """

    def __init__(self):
        """ constructor
            self.jobs is link to /jobsub/acctgroups/<acctgroup>/jobs/
            self.users goes to  /jobsub/acctgroups/<acctgroup>/users/
            and so on
        """
        self.jobs = AccountJobsResource()
        self.users = UsersResource()
        self.help = JobsubHelpResource()
        self.dropbox = DropboxResource()
        self.sandboxes = SandboxesResource()
        self.sites = ConfiguredSitesResource()
        self.authmethods = AuthMethodsResource()

    def doGET(self, acctgroup):
        """ Query list of accounting groups. Returns a JSON list object.
            API is /jobsub/acctgroups/
        """
        if acctgroup is None:
            out = []
            for grp in get_supported_accountinggroups():
                out.append(rel_link(grp))
            return {'out': out}
        else:
            g = acctgroup
            out = ['Accounting group %s' % g,
                   ['<a href=jobs/>running jobs</a>',
                    '<a href=sandboxes/>sandboxes for completed jobs</a>',
                    '<a href=help/>jobsub_submit help options for %s </a>' % g,
                    '<a href=sites/>OSG sites that accept jobs from %s </a>' % g,
                   ]
                  ]

            rc = {'out': out}
            return rc

    @cherrypy.expose
    @format_response
    def index(self, acctgroup=None, **kwargs):
        """index.html
        """
        try:
            subject_dn = get_client_dn()
            if subject_dn is not None:
                logger.log('subject_dn: %s' % subject_dn)
                if cherrypy.request.method == 'GET':
                    rc = self.doGET(acctgroup)
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
        except:
            err = 'Exception on AccountingGroupsResource.index: %s' %\
                sys.exc_info()[1]
            cherrypy.response.status = 500
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR, logfile='error',
                       traceback=True)
            rc = {'err': err}

        return rc
