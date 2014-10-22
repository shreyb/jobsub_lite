import cherrypy
import logger
import os
import time

from jobsub import is_supported_accountinggroup, execute_jobsub_command, get_command_path_root
from format import format_response




@cherrypy.popargs('user_id')
class SandboxesResource(object):


    def doGET(self,user_id=None,kwargs=None):
        """ Query for valid sandboxes for given user/acctgroup.  Returns a JSON list object.
	    API is /jobsub/acctgroups/<grp>/sandboxes/<user_id>/
        """
        acctgroup=None
	if kwargs.has_key('acctgroup'):
		acctgroup=kwargs.get('acctgroup')
	if is_supported_accountinggroup(acctgroup):
		filedict={}
		command_path_root = get_command_path_root()
		p=os.path.join(command_path_root, acctgroup, user_id)
		l=["acctgroup: %s"%acctgroup, "user_id:%s"%user_id,p ]
		for f in os.listdir(p):
		    if f.find('@') > 0:
			fp=os.path.join(p,f)
			t=os.path.getctime(fp)
			filedict[t]=f
		keylist=filedict.keys()
		l=["JobsubJobID, \t\t   CreationDate for user %s in Accounting Group %s"%(user_id,acctgroup)]
		for key in sorted(keylist,key=float):
		    itm="%s \t\t %s"% (filedict[key], time.ctime(key))
		    l.append(itm)
        	return {'out': l}
	else:
                err = 'AccountingGroup %s is not configured in jobsub' % acctgroup
                logger.log(err)
                rc = {'err': err}
                cherrypy.response.status = 500
		return rc


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
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc
