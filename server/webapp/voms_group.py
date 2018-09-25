"""
 Description:
   Query voms prefix (group) of an accounting group as configured on the
   Jobsub server

   API is /acctgroups/<group>/vomsgroup/

 Project:
   JobSub

 Author:
   Shreyas Bhat

"""
import cherrypy
import logger
import logging
from authutils import get_voms
from format import format_response


class VOMSGroupResource(object):
    """see module documentation, only one class in file
    """

    def doGET(self, kwargs):
        """ http GET request on index.html of API
            Query dropbox location. Returns a JSON list object.
            API is /acctgroups/<group>/vomsgroup/
        """
        acctgroup = kwargs.get('acctgroup')
        logger.log('acctgroup=%s' % acctgroup)
        voms_group = get_voms(acctgroup)
        if voms_group is None:
            cherrypy.response.status = 404
            return {'err': 'VOMS Group is NOT found for %s'
                    % acctgroup}
        return {'out': voms_group}

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
            err = 'Exception on VOMSGroupResource.index'
            cherrypy.response.status = 500
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
            rc = {'err': err}

        return rc
