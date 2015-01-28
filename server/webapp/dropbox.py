import cherrypy
import logger
import uuid
import os
import sys
import socket

from util import get_uid
from auth import check_auth
from job import AccountJobsResource
from format import format_response
from jobsub import get_supported_accountinggroups
from jobsub import get_dropbox_path_root
from util import mkdir_p
from util import digest_for_file
from users import UsersResource

from cherrypy.lib.static import serve_file

from shutil import copyfileobj, rmtree




@cherrypy.popargs('box_id', 'filename')
class DropboxResource(object):
    def doGET(self, acctgroup, box_id, filename):
        """ Serve files from Dropbox service
            API is /jobsub/acctgroups/<group_id>/dropbox/<box_id>/<filename>/
        """
        subject_dn = cherrypy.request.headers.get('Auth-User')
        uid = get_uid(subject_dn)
        dropbox_path_root = get_dropbox_path_root()
        dropbox_path = os.path.join(dropbox_path_root, acctgroup, uid)
        dropbox_file_path = os.path.join(dropbox_path, box_id, filename)
        return serve_file(dropbox_file_path, "application/x-download", "attachment")

    def doPOST(self, acctgroup, kwargs):
        """ Upload files to Dropbox service. Return JSON object describing location of files.
            API is /jobsub/acctgroups/<group_id>/dropbox/
        """
        subject_dn = cherrypy.request.headers.get('Auth-User')
        uid = get_uid(subject_dn)
        box_id = str(uuid.uuid4())
        dropbox_path_root = get_dropbox_path_root()
        #dropbox_path = os.path.join(dropbox_path_root, acctgroup, uid, box_id)
        #mkdir_p(dropbox_path)
        file_map = dict()
        for arg_name, arg_value in kwargs.items():
            logger.log("arg_name=%s arg_value=%s"%(arg_name,arg_value))
            if hasattr(arg_value, 'file'):
		#logger.log(dir(arg_value))
                #gets a little tricky here, older clients can supply file0 file1 etc for arg_name
                #new clients supply sha1 hexdigests for arg_name. Check if it already exists in
                #either case
		if arg_name.find('file')<0:
                    supplied_digest=arg_name
                    phldr=arg_name
                else:
                    supplied_digest=False
                    phldr=box_id
                dropbox_path = os.path.join(dropbox_path_root, acctgroup, uid, phldr)
		mkdir_p(dropbox_path)
                dropbox_file_path = os.path.join(dropbox_path, arg_value.filename)
                dropbox_url = '/jobsub/acctgroups/%s/dropbox/%s/%s' % (acctgroup, phldr, arg_value.filename)
                logger.log('dropbox_file_path: %s' % dropbox_file_path)
		if supplied_digest and \
                   os.path.exists(dropbox_file_path) and \
                   supplied_digest==digest_for_file(dropbox_file_path):

                   downloaded=False
                else:
                    with open(dropbox_file_path, 'wb') as dst_file:
                        copyfileobj(arg_value.file, dst_file)
                    downloaded=True
		if not supplied_digest:
                    derived_digest=digest_for_file(dropbox_file_path)
                    new_dropbox_path = os.path.join(dropbox_path_root, acctgroup, uid, derived_digest) 
                    new_dropbox_file_path = os.path.join(dropbox_path_root, acctgroup, uid, derived_digest, arg_value.filename)
                    dropbox_url = '/jobsub/acctgroups/%s/dropbox/%s/%s' % (acctgroup, derived_digest, arg_value.filename)
                    if os.path.exists(new_dropbox_path):
                        rmtree(dropbox_path)
                    else:
                        os.rename(dropbox_path,new_dropbox_path)
                    dropbox_file_path=new_dropbox_file_path

		
                file_map[arg_name] = { 
                        'path': dropbox_file_path, 
                        'url': dropbox_url ,
                        'host':socket.gethostname()
                        }

		logger.log('supplied_digest=%s downloaded=%s digest_for_file=%s'%\
                          (supplied_digest,downloaded,digest_for_file(dropbox_file_path)))

		if supplied_digest and \
                   downloaded and \
                   supplied_digest != digest_for_file(dropbox_file_path):
                    err=" checksum error on %s during transfer "%dropbox_file_path
		    logger.log(err)
                    raise Exception(err)

        return file_map

    @cherrypy.expose
    @format_response
    @check_auth
    def index(self, acctgroup, box_id=None, filename=None, **kwargs):
        try:
            subject_dn = cherrypy.request.headers.get('Auth-User')
            if subject_dn is not None:
                logger.log('subject_dn: %s' % subject_dn)
                if cherrypy.request.method == 'POST':
                    if box_id is None and filename is None:
                        rc = self.doPOST(acctgroup, kwargs)
                    else:
                        err = 'User has supplied box_id and/or filename but POST is for adding files'
                        logger.log(err)
                        rc = {'err': err}
                elif cherrypy.request.method == 'GET':
                    if box_id is not None and filename is not None:
                        rc = self.doGET(acctgroup, box_id, filename)
                    else:
                        err = 'User must supply box_id and filename for GET'
                        logger.log(err)
                        rc = {'err': err}
                else:
                    err = 'Unsupported method: %s' % cherrypy.request.method
                    logger.log(err)
                    rc = {'err': err}
            else:
                # return error for no subject_dn
                err = 'User has not supplied subject dn'
                logger.log(err)
                rc = {'err': err}
        except:
            err = 'Exception on DropboxResource.index:%s' % sys.exc_info()[1]
            cherrypy.response.status = 500
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc

