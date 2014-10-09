import cherrypy
import logger
import sys
import os

from auth import check_auth
from format import format_response
from jobsub import execute_jobsub_command





class VersionResource(object):

    def doGET(self, kwargs):
        jstools_dict=execute_jobsub_command('nova','dude',['--version'])
	if jstools_dict.has_key('out'):
		tools_version='jobsub tools version:%s'% jstools_dict['out'][0]
	else:
		tools_version='jobsub tools version:%s'% jstools_dict['err']
        server_version='jobsub server rpm release %s'%\
		os.environ.get('JOBSUB_SERVER_VERSION')
        return {'out': [server_version, tools_version] }

    @cherrypy.expose
    @format_response
    def index(self,  **kwargs):
        try:
            if cherrypy.request.method == 'GET':
                rc = self.doGET(kwargs)
            else:
                err = 'Unimplemented method: %s' % cherrypy.request.method
                logger.log(err)
                rc = {'err': err}
        except:
            err = 'Exception on VersionResouce.index: %s'%sys.exc_info()[1]
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc

