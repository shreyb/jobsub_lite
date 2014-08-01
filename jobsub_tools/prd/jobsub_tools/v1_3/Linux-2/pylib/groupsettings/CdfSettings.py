#!/usr/bin/env python
# $Id$
import os
import sys
from JobSettings import JobSettings
from optparse import OptionGroup

class CdfSettings(JobSettings):
    def __init__(self):
        super(CdfSettings,self).__init__()


    def initCmdParser(self):
        super(CdfSettings,self).initCmdParser()
        self.cdf_group = OptionGroup(self.cmdParser, "Cdf Specific Options")
        self.cmdParser.add_option_group(self.cdf_group)

        self.cdf_group.add_option("--tarFile", dest="tar_file_name",
                                 action="store",type="string",
                                 help="path for tar file to be submitted (e.g. dropbox://./submitme.tar.gz)")

        self.cdf_group.add_option("--outLocation", dest="outLocation",
                                 action="store",type="string",
                                 help="full path for output file (e.g. me@ncdfxx.fnal.gov:/home/me/out.tgz)")

        self.cdf_group.add_option("--procType", dest="procType",
                                 action="store",type="string",
                                 help="desired process type (e.g. short)")

        self.cdf_group.add_option("--start", dest="start",
                                 action="store",type="string",
                                 help="beginning segment number (e.g. 1)")
              
        self.cdf_group.add_option("--end", dest="end",
                                 action="store",type="string",
                                 help="ending segment number (e.g. 100))")

        self.cdf_group.add_option("--sections", dest="sections",
                                 action="store",type="string",
                                 help="segment range (e.g. 1-100)) start-end, use instead of --start --end")

        self.cdf_group.add_option("--dhaccess", dest="dhaccess",
                                 action="store",type="string",
                                 help="method for dataset access, options are SAM,userSAM,dcache,diskpool,MCGen,rootd,fcp/rcp, None")
        self.cdf_group.add_option("--sam_station", dest="sam_station",
                                 action="store",type="string",
                                 help="=qualifier:version:station. To use a sam station different from the default,to specify only if dhaccess=SAM  is used (default is SAM) ")
                
        self.cdf_group.add_option("--maxParallelSec", dest="maxParallelSec",
                                 action="store",type="string",
                                 help="max parallel running section number (e.g. 30) ")
        self.cdf_group.add_option("--email", dest="email",
                                 action="store",type="string",
                                 help="optional email address for summary output")

        self.cdf_group.add_option("--dataset", dest="dataset_definition",
                                 action="store",type="string",
                                 help="")

        self.cdf_group.add_option("--farm", dest="farm",
                                 action="store",type="string",
                                 help="")

        self.cdf_group.add_option("--group", dest="group",
                                 action="store",type="string",
                                 help="")

        self.cdf_group.add_option("--os", dest="os",
                                 action="store",type="string",
                                 help="")

        self.cdf_group.add_option("--cdfsoft", dest="cdfsoft",
                                 action="store",type="string",
                                 help="")

        self.cdf_group.add_option("--site", dest="site",
                                 action="store",type="string",
                                 help="")

        self.cdf_group.add_option("--donotdrain", dest="donotdrain",
                                 action="store",type="string",
                                 help="")


    def writeToWrapFile(self,list,fh):
        for cmd in list:
	    fh.write("""CMD="%s"\n """%cmd)
            if self.settings['verbose']:
	        fh.write("echo executing: $CMD\n")
	    fh.write("$CMD\n")

    def makeWrapFilePreamble(self):
        super(CdfSettings,self).makeWrapFilePreamble()
        settings=self.settings
	preWrapCommands = [ 
		"export USER=$GRID_USER",
		"export INPUT_TAR_FILE=${_CONDOR_JOB_IWD}/${INPUT_TAR_FILE}",
		"export OUTPUT_TAR_FILE=${USER}.${CLUSTER}.${PROCESS}.tgz",
		"export OUTPUT_DESTINATION=%s"%settings['outLocation'],
                "cd ${TMPDIR}",
	]
        f = open(settings['wrapfile'], 'a')
	if settings['verbose']:
		f.write("###### BEGIN CDFSettings.makeWrapFilePreamble\n")
	self.writeToWrapFile(preWrapCommands,f)
	if settings['verbose']:
        	f.write("###### END CDFSettings.makeWrapFilePreamble\n")
        f.close()

    def makeWrapFile(self):
        #super(CdfSettings,self).makeWrapFile()
        settings=self.settings
	wrapCommands = [ 
		"tar xvzf $INPUT_TAR_FILE",
		"%s $@"%os.path.basename(settings['exe_script']),
		"export EXIT_STATUS=$?",
	]
        f = open(settings['wrapfile'], 'a')
	if settings['verbose']:
        	f.write("###### BEGIN CDFSettings.makeWrapFile\n")
	self.writeToWrapFile(wrapCommands,f)
	if settings['verbose']:
        	f.write("###### END CDFSettings.makeWrapFile\n")
        f.close()


    def makeWrapFilePostamble(self):
        settings=self.settings
	postWrapCommands = [ 
		"tar cvzf ${OUTPUT_TAR_FILE} * ",
		"scp ${OUTPUT_TAR_FILE} ${OUTPUT_DESTINATION}:${OUTPUT_TAR_FILE} ",
	]
        f = open(settings['wrapfile'], 'a')
	if settings['verbose']:
        	f.write("###### BEGIN CDFSettings.makeWrapFilePostamble\n")
	self.writeToWrapFile(postWrapCommands,f)
	if settings['verbose']:
        	f.write("###### END CDFSettings.makeWrapFilePostmble\n")
        f.close()
        super(CdfSettings,self).makeWrapFilePostamble()


    def checkSanity(self):
	settings=self.settings
	if not settings.has_key('outLocation'):
		settings['outLocation']="%s@fcdficaf2.fnal.gov"%settings['user']
	if not settings['tar_file_name']:
		raise Exception ('you must supply an input tar ball using --tarFile')
        return super(CdfSettings,self).checkSanity()
        
