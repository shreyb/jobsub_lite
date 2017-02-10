"""Module:
            dropbox
   Purpose:
            upload/download files from dropbox service
            API is /jobsub/acctgroups/<group_id>/dropbox/
            API is /jobsub/acctgroups/<group_id>/dropbox/<box_id>/<filename>/
  Author:
            Nick Palumbo
"""
import cherrypy
import logger
import logging
import uuid
import os
import sys
import socket
from auth import check_auth
from request_headers import get_client_dn
from format import format_response
from jobsub import get_dropbox_path_root
from util import mkdir_p
from util import digest_for_file

from cherrypy.lib.static import serve_file

from shutil import copyfileobj, rmtree


@cherrypy.popargs('box_id', 'filename')
class DropboxResource(object):

    def doGET(self, acctgroup, box_id, filename):
        """ Serve files from Dropbox service
            API is /jobsub/acctgroups/<group_id>/dropbox/<box_id>/<filename>/
        """
        dropbox_path_root = get_dropbox_path_root()
        dropbox_path = os.path.join(
            dropbox_path_root, acctgroup, cherrypy.request.username)
        drpbx_fpath = os.path.join(dropbox_path, box_id, filename)
        return serve_file(drpbx_fpath,
                          "application/x-download", "attachment")

    def doPOST(self, acctgroup, kwargs):
        """ Upload files to Dropbox service. Return JSON object
            describing location of files.
            API is /jobsub/acctgroups/<group_id>/dropbox/
        """
        box_id = str(uuid.uuid4())
        dropbox_path_root = get_dropbox_path_root()
        file_map = dict()
        for arg_name, arg_value in kwargs.items():
            logger.log("arg_name=%s arg_value=%s" % (arg_name, arg_value))
            if hasattr(arg_value, 'file'):
                if arg_name.find('file') < 0:
                    supplied_digest = arg_name
                    phldr = arg_name
                else:
                    supplied_digest = False
                    phldr = box_id
                dropbox_path = os.path.join(dropbox_path_root, acctgroup,
                                            cherrypy.request.username, phldr)
                mkdir_p(dropbox_path)
                drpbx_fpath = os.path.join(
                    dropbox_path, arg_value.filename)
                dropbox_url = '/jobsub/acctgroups/%s/dropbox/%s/%s' %\
                    (acctgroup, phldr, arg_value.filename)
                logger.log('drpbx_fpath: %s' % drpbx_fpath)
                if supplied_digest and \
                   os.path.exists(drpbx_fpath) and \
                   supplied_digest == digest_for_file(drpbx_fpath):

                    downloaded = False
                else:
                    with open(drpbx_fpath, 'wb') as dst_file:
                        copyfileobj(arg_value.file, dst_file)
                    downloaded = True
                if not supplied_digest:
                    derived_digest = digest_for_file(drpbx_fpath)
                    new_dropbox_path = os.path.join(dropbox_path_root,
                                                    acctgroup,
                                                    cherrypy.request.username,
                                                    derived_digest)
                    new_drpbx_fpath = os.path.join(new_dropbox_path,
                                                   arg_value.filename)
                    dropbox_url = '/jobsub/acctgroups/%s/dropbox/%s/%s' % (
                        acctgroup, derived_digest, arg_value.filename)
                    if os.path.exists(new_dropbox_path):
                        rmtree(dropbox_path)
                    else:
                        os.rename(dropbox_path, new_dropbox_path)
                    drpbx_fpath = new_drpbx_fpath

                file_map[arg_name] = {
                    'path': drpbx_fpath,
                    'url': dropbox_url,
                    'host': socket.gethostname()
                }

                logger.log('supplied_digest=%s downloaded=%s digest_for_file=%s' %
                           (supplied_digest, downloaded,
                            digest_for_file(drpbx_fpath)))

                if supplied_digest and \
                   downloaded and \
                   supplied_digest != digest_for_file(drpbx_fpath):
                    err = "checksum error on %s during transfer " % drpbx_fpath
                    logger.log(err, severity=logging.ERROR)
                    logger.log(err, severity=logging.ERROR, logfile='error')
                    raise Exception(err)

        return file_map

    @cherrypy.expose
    @format_response
    @check_auth
    def index(self, acctgroup, box_id=None, filename=None, **kwargs):
        try:
            if kwargs.get('role'):
                cherrypy.request.role = kwargs.get('role')
            if kwargs.get('username'):
                cherrypy.request.username = kwargs.get('username')
            if kwargs.get('voms_proxy'):
                cherrypy.request.vomsProxy = kwargs.get('voms_proxy')
            subject_dn = get_client_dn()
            if subject_dn is not None:
                logger.log('subject_dn: %s' % subject_dn)
                if cherrypy.request.method == 'POST':
                    if box_id is None and filename is None:
                        rcode = self.doPOST(acctgroup, kwargs)
                    else:
                        err = 'User has supplied box_id and/or filename '
                        err += 'but POST is for adding files'
                        logger.log(err, severity=logging.ERROR)
                        logger.log(err, severity=logging.ERROR,
                                   logfile='error')
                        rcode = {'err': err}
                elif cherrypy.request.method == 'GET':
                    if box_id is not None and filename is not None:
                        rcode = self.doGET(acctgroup, box_id, filename)
                    else:
                        err = 'User must supply box_id and filename for GET'
                        logger.log(err, severity=logging.ERROR)
                        logger.log(err, severity=logging.ERROR,
                                   logfile='error')
                        rcode = {'err': err}
                else:
                    err = 'Unsupported method: %s' % cherrypy.request.method
                    logger.log(err, severity=logging.ERROR)
                    logger.log(err, severity=logging.ERROR, logfile='error')
                    rcode = {'err': err}
            else:
                # return error for no subject_dn
                err = 'User has not supplied subject dn'
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rcode = {'err': err}
        except:
            err = 'Exception on DropboxResource.index:%s' % sys.exc_info()[1]
            cherrypy.response.status = 500
            logger.log(err, severity=logging.ERROR, traceback=True)
            logger.log(err, severity=logging.ERROR,
                       logfile='error', traceback=True)
            rcode = {'err': err}

        return rcode
