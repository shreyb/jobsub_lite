import cherrypy

from job import JobsResource


@cherrypy.popargs('accountinggroup')
class AccountingGroupsResource(object):
    def __init__(self):
        self.jobs = JobsResource()

