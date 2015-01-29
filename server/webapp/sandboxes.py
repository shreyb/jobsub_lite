import cherrypy
import logger
import os
import time
import socket
import sys
import subprocessSupport

from jobsub import is_supported_accountinggroup, get_command_path_root
from format import format_response




@cherrypy.popargs('user_id')
class SandboxesResource(object):


    def doGET(self,user_id=None,kwargs=None):
        """ Query for valid sandboxes for given user/acctgroup.  Returns a JSON list object.
	    API is /jobsub/acctgroups/<grp>/sandboxes/<user_id>/
        """
	command_path_root = get_command_path_root()
        acctgroup='None'
        if kwargs.has_key('acctgroup'):
                acctgroup=kwargs.get('acctgroup')
	if acctgroup !=  'None':
		cmd= "find  %s/%s -maxdepth 1 -name %s"%(command_path_root,acctgroup,user_id)
	else:
		cmd="find  %s -maxdepth 2 -name %s"%(command_path_root,user_id)
	try:
		sandbox_dirs, cmd_err = subprocessSupport.iexe_cmd(cmd)

	except:
		err="No sandboxes found for user %s accounting group %s" %(acctgroup,user_id)
		logger.log(err)
                rc = {'out': err}
                cherrypy.response.status = 404 
		logger.log("%s"%sys.exc_info()[1])
                return rc

	
	l=[]
	for dir in sandbox_dirs.split('\n'):
		filedict={}
		acctgroup=os.path.basename(os.path.dirname(dir))	
		try:
		    for f in os.listdir(dir):
		    	if f.find('@') > 0:
				try:
					fp=os.path.join(dir,f)
					t=os.path.getctime(fp)
					filedict[t]=f
				except:
					logger.log("%s"%sys.exc_info()[1])
		    keylist=filedict.keys()
		    if len(keylist)>0:
			l.append("JobsubJobID, \t\t   CreationDate for user %s in Accounting Group %s"%(user_id,acctgroup))
		    for key in sorted(keylist,key=float):
		    	itm="%s           %s"% (filedict[key], time.ctime(key))
		    	l.append(itm)
		except:
			logger.log("%s"%sys.exc_info()[1])
			
	if len(l)==0:
		host = socket.gethostname()
		return {'out':'no sandbox information found on %s for user %s '%(host,user_id)}
	else:
		logger.log("%s"%l)
        	return {'out': l}


    @cherrypy.expose
    @format_response
    def index(self, user_id=None, **kwargs):
        try:
            subject_dn = cherrypy.request.headers.get('Auth-User')
            logger.log("user_id %s"%user_id)
            logger.log("kwargs %s"%kwargs)
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
