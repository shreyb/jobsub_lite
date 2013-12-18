#!/usr/bin/env python

from ConfigParser import SafeConfigParser
import commands, os, sys, string, tempfile


def findConfigFile():
    predef=os.environ.get("JOBSUB_INI_FILE",None)
    if predef is not None:
	return predef
    jsbtd=os.environ.get("JOBSUB_TOOLS_DIR","")+'/bin'
    pwd=os.environ.get("PWD")
    home=os.environ.get("HOME")
    for dir in [pwd, home, jsbtd]:
        inifile = dir+'/jobsub.ini'
        if os.path.isfile(inifile):
		#if dir != jsbtd:
                #	print "using %s"%inifile
                return inifile
    return None



def runConfig():
    cfile = findConfigFile()
    scp = SafeConfigParser()
    scp.read(cfile)
    exps=scp.sections()
    grp=os.environ.get("GROUP")
    if grp is None:
    	(stat,grp)=commands.getstatusoutput("id -gn")
    user=os.environ.get("USER","fermilab")
    if grp not in exps:
        grp = "fermilab"
    fn = tempfile.mktemp(suffix='.csh')
    fd = open(fn,"w")
    for var in scp.options(grp):
	eval=os.environ.get(var.upper(),None)
	if eval is None:
        	val=scp.get(grp,var)
        	fd.write( "setenv %s  %s\n"%(var.upper(),val))
    submit_host = os.environ.get("SUBMIT_HOST")
    if submit_host is None and scp.has_option(grp,'submit_host'):
	submit_host = scp.get(grp,'submit_host')
    if submit_host is not None:
	if scp.has_section(submit_host):
		for var in scp.options(submit_host):
			eval=os.environ.get(var.upper(),None)
			if eval is None:
				val = scp.get(submit_host,var)
				fd.write("setenv %s %s\n"%(var.upper(),val))
    fd.write("setenv JOBSUB_INI_FILE %s\n"%cfile)
    fd.close()
    print fn


if __name__ == '__main__':
    runConfig()
