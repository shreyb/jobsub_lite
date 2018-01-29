"""
 Description:
   Query dropbox location to use for an experiment to drop tarballs and other files.  
   Written as a part of the transition to unmount Bluearc from the grid worker nodes.

   API is /acctgroups/<group>/dropboxlocation/

 Project:
   JobSub

 Author:
   Shreyas Bhat

"""
import cherrypy
import logger
import logging
import jobsub
from format import format_response


class DropboxLocationResource(object):
    """see module documentation, only one class in file
    """

    def doGET(self, kwargs):
        """ http GET request on index.html of API
            Query dropbox location. Returns a JSON list object.
            API is /acctgroups/<group>/dropboxlocation/ 
        """
        acctgroup = kwargs.get('acctgroup')
        logger.log('acctgroup=%s' % acctgroup)
        dropbox = jobsub.get_dropbox_location(acctgroup)
        if dropbox == False:
            cherrypy.response.status = 403
            return {'err': 'Dropbox location is NOT available for %s'
                % acctgroup}
        elif not dropbox:
            cherrypy.response.status = 404
            return {'err': 'Dropbox location is NOT found for %s'
                % acctgroup}
        return {'out': dropbox}

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
            err = 'Exception on DropboxLocationResource.index'
            cherrypy.response.status = 500
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
            rc = {'err': err}

        return rc
