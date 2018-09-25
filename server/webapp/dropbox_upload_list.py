"""
 Description:
   Query list of files uploaded to dropbox by jobsub for an experiment

   API is /acctgroups/<group>/dropboxuploadlist/

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


class DropboxUploadListResource(object):
    """see module documentation, only one class in file
    """

    def doGET(self, kwargs):
        """ http GET request on index.html of API
            Query dropbox location. Returns a JSON list object.
            API is /acctgroups/<group>/dropboxuploadlist/
        """
        acctgroup = kwargs.get('acctgroup')
        logger.log('acctgroup=%s' % acctgroup)
        dropbox_uploads = jobsub.get_dropbox_upload_list(acctgroup)
        if dropbox_uploads == False:
            cherrypy.response.status = 403
            return {'err': 'Dropbox location is NOT available for %s'
                    % acctgroup}
        # Case for if dropbox_uploads is empty
        elif not dropbox_uploads:
            cherrypy.response.status = 404
            return {'err': 'Dropbox upload list is NOT found for %s'
                    % acctgroup}
        return {'out': dropbox_uploads}

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
        except Exception:
            err = 'Exception on DropboxUploadListResource.index'
            cherrypy.response.status = 500
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
            rc = {'err': err}

        return rc
