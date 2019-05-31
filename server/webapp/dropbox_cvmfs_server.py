"""
 Description:
   Query server for name of dropbox cvmfs server to distribute tarballs from.  

   API is /acctgroups/<group>/dropboxcvmfsserver/

 Project:
   JobSub

 Author:
   Dennis Box

"""
import cherrypy
import logger
import logging
import jobsub
from format import format_response


class DropboxCVMFSServerResource(object):
    """see module documentation, only one class in file
    """

    def doGET(self, kwargs):
        """ http GET request on index.html of API
            Query dropbox location. Returns a JSON list object.
            API is /acctgroups/<group>/dropboxlocation/ 
        """
        acctgroup = kwargs.get('acctgroup')
        logger.log('acctgroup=%s' % acctgroup)
        dropbox_server = jobsub.get_dropbox_cvmfs_server(acctgroup)
        if dropbox_server == False:
            cherrypy.response.status = 403
            return {'err': 'Dropbox server is NOT available for %s'
                % acctgroup}
        elif not dropbox_server:
            cherrypy.response.status = 404
            return {'err': 'Dropbox server is NOT found for %s'
                % acctgroup}
        return {'out': dropbox_server}

    @cherrypy.expose
    @format_response
    def index(self, **kwargs):
        """index.html, only GET implemented
        """
        try:
            logger.log("kwargs %s" % kwargs)

            if cherrypy.request.method == 'GET':
                rc = self.doGET(kwargs)
            else:
                err = 'Unsupported method: %s' % cherrypy.request.method
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rc = {'err': err}
        except:
            err = 'Exception on DropboxCVMFSServerResource.index'
            cherrypy.response.status = 500
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
            rc = {'err': err}

        return rc
