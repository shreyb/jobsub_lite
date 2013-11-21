import cherrypy
import logger

from job import JobsResource

from JobsubConfigParser import JobsubConfigParser


def is_supported_accountinggroup(accountinggroup):
    rc = False
    try:
        p = JobsubConfigParser()
        groups = p.supportedGroups()
        rc = (accountinggroup in groups)
    except:
        logger.log('Failed to get accounting groups: ', traceback=True)

    return rc


@cherrypy.popargs('accountinggroup')
class AccountingGroupsResource(object):
    def __init__(self):
        self.jobs = JobsResource()

