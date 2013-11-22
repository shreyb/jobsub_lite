import cherrypy

from job import JobsResource


@cherrypy.popargs('acctgroup')
class AccountingGroupsResource(object):
    def __init__(self):
        self.jobs = JobsResource()

