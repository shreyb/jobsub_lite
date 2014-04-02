import cherrypy
import logger
import uuid
import os

from util import get_uid
from auth import check_auth
from job import AccountJobsResource
from format import format_response
from jobsub import get_supported_accountinggroups
from jobsub import execute_jobsub_command
from jobsub import get_dropbox_path_root
from util import mkdir_p

from cherrypy.lib.static import serve_file

from shutil import copyfileobj


class HelpResource(object):
    def doGET(self, acctgroup):
        """ Executes the jobsub tools command with the help argument and returns the output.
            API call is /jobsub/acctgroups/<group_id>/help
        """
        jobsub_args = ['--help']
        subject_dn = cherrypy.request.headers.get('Auth-User')
        uid = get_uid(subject_dn)
        rc = execute_jobsub_command(acctgroup, uid, jobsub_args)

        return rc


    @cherrypy.expose
    @format_response
    def index(self, acctgroup, **kwargs):
        try:
            subject_dn = cherrypy.request.headers.get('Auth-User')
            if subject_dn is not None:
                logger.log('subject_dn: %s' % subject_dn)
                if cherrypy.request.method == 'GET':
                    rc = self.doGET(acctgroup)
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
            err = 'Exception on JobsResouce.index'
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc


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
        dropbox_path = os.path.join(dropbox_path_root, acctgroup, uid, box_id)
        mkdir_p(dropbox_path)
        file_map = dict()
        for arg_name, arg_value in kwargs.items():
            if hasattr(arg_value, 'file'):
                dropbox_file_path = os.path.join(dropbox_path, arg_value.filename)
                dropbox_url = '/jobsub/acctgroups/%s/dropbox/%s/%s' % (acctgroup, box_id, arg_value.filename)
                logger.log('dropbox_file_path: %s' % dropbox_file_path)
                with open(dropbox_file_path, 'wb') as dst_file:
                    copyfileobj(arg_value.file, dst_file)
                    file_map[arg_name] = { 'path': dropbox_file_path, 'url': dropbox_url }

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
            err = 'Exception on JobsResouce.index'
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc


@cherrypy.popargs('acctgroup')
class AccountingGroupsResource(object):
    def __init__(self):
        self.jobs = AccountJobsResource()
        self.help = HelpResource()
        self.dropbox = DropboxResource()

    def doGET(self, acctgroup):
        """ Query list of accounting groups. Returns a JSON list object.
            API is /jobsub/acctgroups/
        """
        if acctgroup is None:
            return {'out': get_supported_accountinggroups()}
        else:
            # No action at this time
            pass

    @cherrypy.expose
    @format_response
    def index(self, acctgroup=None, **kwargs):
        try:
            subject_dn = cherrypy.request.headers.get('Auth-User')
            if subject_dn is not None:
                logger.log('subject_dn: %s' % subject_dn)
                if cherrypy.request.method == 'GET':
                    rc = self.doGET(acctgroup)
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
            err = 'Exception on JobsResouce.index'
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc
