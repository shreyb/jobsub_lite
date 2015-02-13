import cherrypy
import logger
import os
import time
import socket
import sys
import subprocessSupport
from JobsubConfigParser import JobsubConfigParser
from jobsub import is_supported_accountinggroup,  get_command_path_root
from format import format_response




@cherrypy.popargs('user_id')
class ConfiguredSitesResource(object):


    def doGET(self,user_id=None,kwargs=None):
        """ Query for configured remote submission sites given acctgroup.  Returns a JSON list object.
	    API is /jobsub/acctgroups/<grp>/configuredsites/
        """
        acctgroup=None
	if kwargs.has_key('acctgroup'):
		acctgroup=kwargs.get('acctgroup')
	if is_supported_accountinggroup(acctgroup):
		site_list=[]
		try:
			p=JobsubConfigParser()
			#pool="-pool fifebatchgpvmhead1.fnal.gov"
			pool=p.get('default','pool_string')
			if pool is None:
				pool=''
			
			try:
				exclude_list=p.get(acctgroup,'site_ignore_list')
			except:
				exclude_list=p.get(p.submit_host(),'site_ignore_list')
			
			cmd="""condor_status %s  -any """ % pool
			cmd=cmd+"""-constraint '(glideinmytype=="glideresource")&&"""
			cmd=cmd+"""(stringlistimember("%s",GLIDEIN_Supported_VOs,",")||stringlistimember("fermilab",GLIDEIN_Supported_VOs,","))&&""" % acctgroup
			cmd=cmd+"""glidein_site=!=UNDEFINED'"""
			cmd=cmd+""" -format '%s\n'  glidein_site """
			logger.log(cmd)
			site_list=[]
			#exclude_list=site_ignore_list(acctgroup)
			logger.log('exclude_list:%s'%exclude_list)
			site_data, cmd_err = subprocessSupport.iexe_cmd(cmd)
        		site_data=site_data.split('\n')
        		for dat in site_data:
                		if dat not in site_list and dat not in exclude_list:
					logger.log('adding %s'%dat)
                        		site_list.append(dat)


		except:
			logger.log("%s"%sys.exc_info()[1])
		if len(site_list)==0:
			host = socket.gethostname()
			return {'out':'no site  information found on %s for accounting_group %s'%(host,acctgroup)}
		else:
        		return {'out': site_list}
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
            err = 'Exception on ConfiguredSitesResource.index'
            logger.log(err, traceback=True)
            rc = {'err': err}

        return rc
