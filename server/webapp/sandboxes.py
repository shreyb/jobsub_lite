import cherrypy
import logger
import os
import time
import socket
import sys
import subprocessSupport
from auth import check_auth, get_client_dn
from jobsub import is_supported_accountinggroup, get_command_path_root
from format import format_response



@cherrypy.popargs('user_id')

class SandboxesResource(object):


    def doGET(self,user_id=None,kwargs=None):
        """ Query for valid sandboxes for given user/acctgroup.  Returns a JSON list object.
        API is /jobsub/acctgroups/<grp>/sandboxes/<user_id>/
        """
        command_path_root = get_command_path_root()
        cmd= "find  %s/%s -maxdepth 1 -name %s"%\
            (command_path_root,cherrypy.request.acctgroup,user_id)
        try:
            sandbox_dirs, cmd_err = subprocessSupport.iexe_cmd(cmd)

        except:
            err="No sandboxes found for user %s accounting group %s" %\
                (user_id, cherrypy.request.acctgroup)
            logger.log(err)
            rc = {'out': err}
            cherrypy.response.status = 404 
            logger.log("%s"%sys.exc_info()[1])
            return rc

        filelist = []
        outlist = []
        for dir in sandbox_dirs.split('\n'):
            acctgroup=os.path.basename(os.path.dirname(dir))
            try:
                for f in os.listdir(dir):
                    if f.find('@') > 0:
                        try:
                            fp=os.path.join(dir,f)
                            t=os.path.getctime(fp)
                            itm=(f, t)
                            filelist.append(itm)
                        except:
                            logger.log("%s"%sys.exc_info()[1])
                if filelist:
                    filelist.sort(key = lambda itm: itm[1])
                    outlist.append("JobsubJobID, \t\t   CreationDate for user %s in Accounting Group %s"%(user_id,acctgroup))
                    for itm in filelist:
                        outlist.append("%s   %s" % (itm[0],time.ctime(itm[1])))
            except:
                logger.log("%s"%sys.exc_info()[1])

            if outlist:
                return {'out': outlist}
            else:
                host = socket.gethostname()
                return {'out':'no sandbox information found on %s for user %s '%(host,user_id)}


    @cherrypy.expose
    @format_response
    @check_auth

    def index(self, acctgroup, **kwargs):
        try:
            cherrypy.request.role = kwargs.get('role')
            cherrypy.request.username = kwargs.get('username')
            cherrypy.request.vomsProxy = kwargs.get('voms_proxy')
            cherrypy.request.acctgroup = acctgroup
            subject_dn = get_client_dn()
            user_id = kwargs.get('user_id')
            logger.log("user_id %s"%user_id)
            logger.log("kwargs %s"%kwargs)
            user_id = cherrypy.request.username

            if subject_dn is not None:
                logger.log('subject_dn: %s' % subject_dn)
                if cherrypy.request.method == 'GET':
                    rc = self.doGET(user_id,kwargs)
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
            err = 'Exception on SandboxesResource.index'
            cherrypy.response.status = 500
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc
