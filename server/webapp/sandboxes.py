"""
 Description:
   This module implements jobsub_fetchlog --list-sandboxes

 Project:
   JobSub

 Author:
   Dennis Box

"""
import cherrypy
import logger
import logging
import os
import time
import socket
import sys
import subprocessSupport
from auth import check_auth
from request_headers import get_client_dn
from request_headers import uid_from_client_dn
from jobsub import get_command_path_root
from jobsub import sandbox_readable_by_group
from jobsub import sandbox_allowed_browsable_file_types
from jobsub import is_superuser_for_group
from jobsub import is_global_superuser
from sandbox import make_sandbox_readable
from format import format_response, rel_link


@cherrypy.popargs('user_id', 'job_id', 'file_id')
class SandboxesResource(object):

    def doGET(self, user_id=None, job_id=None, file_id=None, kwargs=None):
        """ Query for valid sandboxes for given user/acctgroup.  Returns a JSON list object.
        API is /jobsub/acctgroups/<grp>/sandboxes/<user_id>/
        """
        command_path_root = get_command_path_root()
        if file_id or job_id:
            allowed_list = sandbox_allowed_browsable_file_types()
            sandbox_dir = "%s/%s/%s/%s" %\
                (command_path_root, cherrypy.request.acctgroup, user_id, job_id)
            make_sandbox_readable(sandbox_dir, user_id)

        if file_id:
            suffix = ".%s" % file_id.split('.')[-1]
            if suffix in allowed_list:
                cherrypy.request.output_format = 'pre'
                cmd = "find  %s/%s/%s/%s/%s -type f -mindepth 0 -maxdepth 0 -exec cat -u {} \;" %\
                    (command_path_root, cherrypy.request.acctgroup,
                     user_id, job_id, file_id)
            else:
                return {'out': 'you do not have permission to browse %s' % file_id}
        elif job_id:
            cmd = "find  %s/%s/%s/%s/ -maxdepth 1 -mindepth 1 -ls" %\
                (command_path_root, cherrypy.request.acctgroup, user_id, job_id)
        elif user_id:
            cmd = "find  %s/%s/%s -maxdepth 1 -mindepth 1 -type l" %\
                (command_path_root, cherrypy.request.acctgroup, user_id)
        else:
            cmd = "find  %s/%s -maxdepth 1 -mindepth 1 -type d" %\
                (command_path_root, cherrypy.request.acctgroup)
        try:
            logger.log(cmd)
            cmd_out, cmd_err = subprocessSupport.iexe_cmd(cmd)

        except:
            err = "No sandboxes found for user %s accounting group %s" %\
                (user_id, cherrypy.request.acctgroup)
            logger.log(err)
            rc = {'out': err}
            cherrypy.response.status = 404
            logger.log("%s" % sys.exc_info()[1], severity=logging.ERROR)
            logger.log("%s" % sys.exc_info()[1],
                       severity=logging.ERROR,
                       logfile='error')
            return rc

        filelist = []
        outlist = []
        for line in cmd_out.split('\n'):
            if file_id:
                outlist.append(line)
            elif job_id:
                parts = line.split()
                if len(parts):
                    filename = os.path.basename(parts[-1])
                    p2 = parts[-5:-1]
                    suffix = ".%s" % filename.split('.')[-1]
                    if suffix in allowed_list:
                        p2.insert(0, rel_link(filename))
                    else:
                        p2.insert(0, filename)
                    outlist.append(' '.join(p2))
            elif user_id:
                fp = line
                f = os.path.basename(line)
                if f.find('@') > 0:
                    try:
                        t = os.path.getmtime(fp)
                        itm = (rel_link(f), t)
                        filelist.append(itm)
                    except:

                        logger.log("%s" % sys.exc_info()[1],
                                   severity=logging.ERROR)

                        logger.log("%s" % sys.exc_info()[1],
                                   severity=logging.ERROR,
                                   logfile='error')
            else:
                d = os.path.basename(line)
                outlist.append(rel_link(d))

        if filelist:
            filelist.sort(key=lambda itm: itm[1])
            #acctgroup = os.path.basename(os.path.dirname(line))
            outlist.append("JobsubJobID CreationDate for user %s in Accounting Group %s" %
                           (user_id, cherrypy.request.acctgroup))
            for itm in filelist:
                outlist.append("%s   %s" % (itm[0], time.ctime(itm[1])))
        if outlist:
            return {'out': outlist}
        else:
            host = socket.gethostname()
            return {'out': 'no sandbox information found on %s for user %s ' % (
                host, user_id)}

    @cherrypy.expose
    @format_response
    @check_auth
    def index(self, acctgroup, **kwargs):
        try:
            if kwargs.get('username'):
                requestor = kwargs.get('username')
            else:
                try:
                    requestor = cherrypy.request.username
                except:
                    requestor = None
                if not requestor:
                    requestor = uid_from_client_dn()

            cherrypy.request.acctgroup = acctgroup
            subject_dn = get_client_dn()
            user_id = kwargs.get('user_id')
            job_id = kwargs.get('job_id')
            file_id = kwargs.get('file_id')
            if user_id != requestor:
                allowed = sandbox_readable_by_group(acctgroup) or \
                          is_superuser_for_group(acctgroup,requestor) or \
                          is_global_superuser(requestor)
                if not allowed:
                    if not user_id:
                        user_id = 'other user'
                    grinfo = "%s may only look at  thier own output for group %s." %\
                        (rel_link(requestor), acctgroup)
                    grinfo += "This is configurable, please open a service desk "
                    grinfo += "ticket if you want this changed"
                    user_id = requestor
                    rc = {'out': grinfo}
                    return rc

            if subject_dn is not None:
                logger.log('subject_dn: %s' % subject_dn)
                if cherrypy.request.method == 'GET':
                    rc = self.doGET(user_id, job_id, file_id, kwargs)
                else:
                    err = 'Unsupported method: %s' % cherrypy.request.method
                    logger.log(err, severity=logging.ERROR)
                    logger.log(err, severity=logging.ERROR, logfile='error')
                    rc = {'err': err}
            else:
                # return error for no subject_dn
                err = 'User has not supplied subject dn'
                logger.log(err, severity=logging.ERROR)
                logger.log(err, severity=logging.ERROR, logfile='error')
                rc = {'err': err}
        except:
            err = 'Exception on SandboxesResource.index'
            cherrypy.response.status = 500
            logger.log(err, traceback=True, severity=logging.ERROR)
            logger.log(err, traceback=True,
                       severity=logging.ERROR,
                       logfile='error')
            rc = {'err': err}

        return rc
