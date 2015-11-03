#!/usr/bin/env python

from ConfigParser import SafeConfigParser
from JobsubConfigParser import *
import commands, os, sys, string, tempfile




def runConfig():
    grp=os.environ.get("GROUP")
    if grp is None:
    	(stat,grp)=commands.getstatusoutput("id -gn")
    user=os.environ.get("USER","fermilab")
    fn = tempfile.mktemp(suffix='.sh')
    fd = open(fn,"w")
    submit_host = os.environ.get("SUBMIT_HOST")
    scp=JobsubConfigParser(grp,submit_host)
    if submit_host is None and scp.has_option(grp,'submit_host'):
    	submit_host = scp.get(grp,'submit_host')

    if scp.has_section(grp):
        if scp.has_option(grp,'group'):
            val=scp.get(grp,'group')
            fd.write( "export GROUP=%s\n"%(val))

    jobsub_ini_vars="JOBSUB_INI_VARS "
    if submit_host is not None:
	if scp.has_section(submit_host):
		for var in scp.options(submit_host):
			eval=os.environ.get(var.upper(),None)
			if eval is None :
	        		val=scp.get(submit_host,var)
				if len(val)==0 or val.find(' ')>=0:
					val="'%s'"%val
        			fd.write( "setenv %s %s\n"%(var.upper(),val))
				jobsub_ini_vars=jobsub_ini_vars+var.upper()+" "
    fd.write("setenv JOBSUB_INI_FILE %s\n"%scp.iniFile())
    fd.write("setenv JOBSUB_INI_VARS='%s'\n"%jobsub_ini_vars)
    fd.close()
    print fn

if __name__ == '__main__':
    runConfig()
