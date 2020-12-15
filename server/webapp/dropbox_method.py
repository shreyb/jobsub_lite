"""
 Description:
   Query dropbox default method (pnfs or cvmfs) for  experiment to drop
   tarballs and other files.

   API is /acctgroups/<group>/dropboxmethod/

 Project:
   JobSub

 Author:
   Dennis Box

"""
import logging
import cherrypy
import logger
import jobsub
from format import format_response


class DropboxMethodResource(object):
    """see module documentation, only one class in file
    """

    def doGET(self, kwargs):
        """ http GET request on index.html of API
            Query dropbox method. Returns a JSON list object.
            API is /acctgroups/<group>/dropboxmethod/
        """
        acctgroup = kwargs.get('acctgroup')
        logger.log('acctgroup=%s' % acctgroup)
        dropbox = jobsub.get_dropbox_method(acctgroup)
        if not dropbox:
            cherrypy.response.status = 404
            return {'err': 'Dropbox method  NOT found for %s'
                           % acctgroup}
        return {'out': dropbox}

    @cherrypy.expose
    @format_response
    def index(self, **kwargs):
        """index.html, only GET implemented
        """
        try:

            if cherrypy.request.method == 'GET':
                rcd = self.doGET(kwargs)
            else:
                err = 'Unsupported method: %s' % cherrypy.request.method
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rcd = {'err': err}
        except BaseException:
            err = 'Exception on DropboxMethodResource.index'
            cherrypy.response.status = 500
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
            rcd = {'err': err}

        logger.log("returning  %s" % rcd)
        return rcd
