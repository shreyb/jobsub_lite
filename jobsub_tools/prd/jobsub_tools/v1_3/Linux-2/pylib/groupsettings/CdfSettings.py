#!/usr/bin/env python
# $Id$
import os
import sys
import re
from JobSettings import JobSettings, UnknownInputError, IllegalInputError, InitializationError

from optparse import OptionGroup

class CdfSettings(JobSettings):
    def __init__(self):
        super(CdfSettings,self).__init__()
        self.settings['usedagman']=True


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

        self.cdf_group.add_option("--start", dest="firstSection",
            action="store",type="int",
            help="beginning segment number (e.g. 1)")
              
        self.cdf_group.add_option("--end", dest="lastSection",
            action="store",type="int",
            help="ending segment number (e.g. 100))")

        self.cdf_group.add_option("--sections", dest="sectionList",
            action="store",type="string",
            help="segment range (e.g. 1-100)) start-end, use instead of --start --end")

        self.cdf_group.add_option("--dhaccess", dest="dhaccess",
            action="store",type="string",
            help="method for dataset access, options are SAM,userSAM,dcache,diskpool,MCGen,rootd,fcp/rcp, None")
        self.cdf_group.add_option("--sam_station", dest="sam_station",
            action="store",type="string",
            help="=qualifier:version:station. To use a sam station different from the default,to specify only if dhaccess=SAM  is used (default is SAM) ")
                
        self.cdf_group.add_option("--maxParallelSec", dest="maxConcurrent",
            action="store",type="string",
            help="max parallel running section number (e.g. 30) ")

        self.cdf_group.add_option("--email", dest="notify_user",
            action="store",type="string",
            help="optional email address for summary output")

        self.cdf_group.add_option("--dataset", dest="dataset_definition",
            action="store",type="string",
            help="")

        self.cdf_group.add_option("--farm", dest="farm",
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

        self.cdf_group.add_option("--donotdrain", dest="drain",
            action="store_false",
            help="")


    def writeToWrapFile(self,list,fh):
        for cmd in list:
            #if self.settings['verbose']:
            if False:
                fh.write("""CMD="%s"\n """%cmd)
                fh.write("echo executing: $CMD\n")
                fh.write("$CMD\n")
            else:
                fh.write("%s\n"%cmd)

    def makeWrapFilePreamble(self):
        super(CdfSettings,self).makeWrapFilePreamble()
        settings=self.settings
        preWrapCommands = [ 
            "export USER=$GRID_USER",
            "export CAF_JID=${DAGMANJOBID}",
            "export OUTPUT_TAR_FILE=jobsub_cdf_output.tgz",
            "#replace '$' in OUTPUT_DESTINATION with literal ${CAF_SECTION}-${CAF_JID} value", 
            "OUTPUT_DESTINATION=%s"%settings['outLocation'],
            "OUTPUT_DESTINATION=`echo $OUTPUT_DESTINATION | sed -e 's/\\\$/\$\{CAF_SECTION\}\-\$\{CAF_JID\}/g'`",
            "eval OUTPUT_DESTINATION=$OUTPUT_DESTINATION ",
            "export OUTPUT_DESTINATION",
            "export HOME=${TMPDIR}/work",
            "mkdir -p ${HOME}",
            "cd ${TMPDIR}/work",
            "#change any '$' in input to ${CAF_SECTION}-1",
            'ARGS=( $args ) ',
            "j=0",
            "for i in ${ARGS[@]}; do",
            '      if [ "$i" = "$" ]; then',
            "            ARGS[$j]=`expr ${CAF_SECTION} - 1`",
            "      fi",
            "      j=`expr $j + 1`",
            "done",
            "set -- ${ARGS[@]}",
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
            "echo executing in directory",
            "pwd",
            "echo its contents:",
            "find . -ls  ",
            "echo untarring $INPUT_TAR_FILE",
            """ if [ -e "$INPUT_TAR_FILE" ]; then tar xvf "$INPUT_TAR_FILE" ; fi""",
            "echo contents after untar:",
            "find . -ls  ",
            """export JOBSUB_USER_SCRIPT=`find . -name %s -print`    """%os.path.basename(settings['exe_script']),
            """echo executing: $JOBSUB_USER_SCRIPT "$@"   """,
            """$JOBSUB_USER_SCRIPT "$@"   """,
            "export JOB_RET_STATUS=$?",
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
            "cp ${JSB_TMP}/JOBSUB_LOG_FILE ./job_${CAF_SECTION}.out",
            "cp ${JSB_TMP}/JOBSUB_ERR_FILE ./job_${CAF_SECTION}.err",
            "tar cvzf ${OUTPUT_TAR_FILE} * ",
            """CPY_OUT="scp ${OUTPUT_TAR_FILE} ${OUTPUT_DESTINATION}"  """,
            "echo executing:$CPY_OUT",
            """
            NTRIES=3
            LSTAT=1
            for ITRY in `seq $NTRIES`
            do
              $CPY_OUT
              LSTAT=$?
              if [ $LSTAT -eq 0 ]; then break; fi
              sleep 600
            done
            """,
        ]
        f = open(settings['wrapfile'], 'a')
        if settings['verbose']:
            f.write("###### BEGIN CDFSettings.makeWrapFilePostamble\n")
        self.writeToWrapFile(postWrapCommands,f)
        if settings['verbose']:
            f.write("###### END CDFSettings.makeWrapFilePostmble\n")
        f.close()
        super(CdfSettings,self).makeWrapFilePostamble()

    def makeCommandFile(self,job_iter=0):
        settings=self.settings
        if job_iter>0:
            tag='CAF_JOB_START_SECTION=([0-9]+)\;CAF_SECTION=([0-9]+)\;CAF_JOB_END_SECTION=([0-9]+)'
            x=settings['environment']
            y=re.sub(tag,"",x)
            this_section=job_iter+settings['firstSection']-1
            sect="CAF_JOB_START_SECTION=%s;CAF_SECTION=%s;CAF_JOB_END_SECTION=%s"%(settings['firstSection'],this_section,settings['lastSection'])
            y2=y+";"+sect
            y=re.sub(";;",";",y2)
            settings['environment'] = y
        super(CdfSettings,self).makeCommandFile(job_iter)

    def checkSanity(self):
        settings=self.settings
        if not settings.has_key('outLocation'):
            settings['outLocation']="%s@fcdficaf2.fnal.gov:%s_$.tgz"%(settings['user'],settings['local_host'])
        if not settings.has_key('tar_file_name'):
            raise Exception ('you must supply an input tar ball using --tarFile')
        if settings.has_key('sectionList'):
            try:
                #print 'sectionList %s'%settings['sectionList']
                firstSection,lastSection=settings['sectionList'].split('-')
                #print 'first: %s last:%s'%(firstSection,lastSection)
                firstSection=int(firstSection)
                lastSection=int(lastSection)
                settings['firstSection']=firstSection
                settings['lastSection']=lastSection
                settings['queuecount']=lastSection-firstSection+1
                settings['job_count']=lastSection-firstSection+1
            except:
                err="error, --sections='%s' must be of the form 'i-j' "%settings['sectionList']
                err=err+"where both i and j are positive integers"
                raise InitializationError(err)

        if settings.has_key('lastSection'):

            if settings['lastSection'] < 1:
                err = "--end value must be greater than 1"
                raise InitializationError(err)
        else:
            settings['lastSection']=settings['queuecount']

        if not settings.has_key('firstSection'):
            settings['firstSection']=1

        numJobs=settings['lastSection']-settings['firstSection']+1
        settings['queuecount']=numJobs
        settings['job_count']=numJobs

        if settings.has_key('firstSection') and not settings.has_key('lastSection'):
            err='you must specify a --end value if you specify a --start one'
            raise InitializationError(err)

        if settings.has_key('firstSection') and settings.has_key('lastSection'):
            if settings['lastSection'] < settings['firstSection']:
                err = " --end value must be greater than or equal to  --start value"
                raise InitializationError(err)
            elif settings['firstSection']<1:
                err = " --start value must be greater than or equal to 1"
                raise InitializationError(err)
            else:
                numJobs=settings['lastSection']-settings['firstSection']+1
                settings['queuecount']=numJobs
                settings['job_count']=numJobs

        if not settings.has_key('firstSection'):
            settings['firstSection']=1
        if not settings.has_key('lastSection'):
            settings['lastSection']=settings['queuecount']
        if not settings.has_key('job_count'):
            settings['job_count']=settings['queuecount']

                     
        return super(CdfSettings,self).checkSanity()
        
