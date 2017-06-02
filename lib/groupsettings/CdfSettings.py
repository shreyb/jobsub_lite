#!/usr/bin/env python
# $Id$
import os
import sys
import re
from JobSettings import JobSettings, UnknownInputError, IllegalInputError, InitializationError

from optparse import OptionGroup


class CdfSettings(JobSettings):

    def __init__(self):
        super(CdfSettings, self).__init__()
        self.settings['usedagman'] = True

    def initCmdParser(self):
        super(CdfSettings, self).initCmdParser()
        self.cdf_group = OptionGroup(self.cmdParser, "Cdf Specific Options")
        self.cmdParser.add_option_group(self.cdf_group)

        self.cdf_group.add_option("--tarFile", dest="tar_file_name",
                                  action="store", type="string",
                                  help="path for tar file to be submitted (e.g. dropbox://./submitme.tar.gz)")

        self.cdf_group.add_option("--outLocation", dest="outLocation",
                                  action="store", type="string",
                                  help="full path for output file (e.g. me@ncdfxx.fnal.gov:/home/me/out.tgz)")

        self.cdf_group.add_option("--procType", dest="procType",
                                  action="store", type="string",
                                  help="desired process type (e.g. short)")

        self.cdf_group.add_option("--start", dest="firstSection",
                                  action="store", type="int",
                                  help="beginning segment number (e.g. 1)")

        self.cdf_group.add_option("--end", dest="lastSection",
                                  action="store", type="int",
                                  help="ending segment number (e.g. 100))")

        self.cdf_group.add_option("--sections", dest="sectionList",
                                  action="store", type="string",
                                  help="segment range (e.g. 1-100)) start-end, use instead of --start --end")

        self.cdf_group.add_option("--dhaccess", dest="dhaccess",
                                  action="store", type="string",
                                  help="method for dataset access, options are SAM,userSAM,dcache,diskpool,MCGen,rootd,fcp/rcp, None")
        self.cdf_group.add_option("--sam_station", dest="sam_station",
                                  action="store", type="string",
                                  help="=qualifier:version:station. To use a sam station different from the default,to specify only if dhaccess=SAM  is used (default is SAM) ")

        self.cdf_group.add_option("--maxParallelSec", dest="maxConcurrent",
                                  action="store", type="string",
                                  help="max parallel running section number (e.g. 30) ")

        self.cdf_group.add_option("--email", dest="notify_user",
                                  action="store", type="string",
                                  help="optional email address for summary output")

        self.cdf_group.add_option("--dataset", dest="dataset_definition",
                                  action="store", type="string",
                                  help="")

        self.cdf_group.add_option("--farm", dest="farm",
                                  action="store", type="string",
                                  help="")

        self.cdf_group.add_option("--os", dest="os",
                                  action="store", type="string",
                                  help="")

        self.cdf_group.add_option("--cdfsoft", dest="cdfsoft",
                                  action="store", type="string",
                                  help="")

        self.cdf_group.add_option("--site", dest="site",
                                  action="store", type="string",
                                  help="")

        self.cdf_group.add_option("--donotdrain", dest="drain",
                                  action="store_false",
                                  help="")

    def writeToWrapFile(self, list, fh):
        for cmd in list:
            # if self.settings['verbose']:
            if False:
                fh.write("""CMD="%s"\n """ % cmd)
                fh.write("echo executing: $CMD\n")
                fh.write("$CMD\n")
            else:
                fh.write("%s\n" % cmd)

    def makeWrapFilePreamble(self):
        super(CdfSettings, self).makeWrapFilePreamble()
        settings = self.settings
        preWrapCommands = [
            "export USER=$GRID_USER",
            "export CAF_JID=${DAGMANJOBID}",
            "export OUTPUT_TAR_FILE=jobsub_cdf_output.tgz",
            "#replace '$' in OUTPUT_DESTINATION with literal ${CAF_SECTION}-${CAF_JID} value",
            "OUTPUT_DESTINATION=%s" % settings['outLocation'],
            "OUTPUT_DESTINATION=`echo $OUTPUT_DESTINATION | sed -e 's/\\\$/\$\{CAF_SECTION\}\-\$\{CAF_JID\}/g'`",
            "eval OUTPUT_DESTINATION=$OUTPUT_DESTINATION ",
            "export OUTPUT_DESTINATION",
            "export HOME=${TMPDIR}/work",
            "mkdir -p ${HOME}",
            "cd ${TMPDIR}/work",
            "#change any '$' in input to ${CAF_SECTION}",
            'ARGS=( $args ) ',
            "j=0",
            "for i in ${ARGS[@]}; do",
            '      if [ "$i" = "$" ]; then',
            "            ARGS[$j]=`expr ${CAF_SECTION} `",
            "      fi",
            "      j=`expr $j + 1`",
            "done",
            "set -- ${ARGS[@]}",
        ]
        f = open(settings['wrapfile'], 'a')
        if settings['verbose']:
            f.write("###### BEGIN CDFSettings.makeWrapFilePreamble\n")
        self.writeToWrapFile(preWrapCommands, f)
        if settings['verbose']:
            f.write("###### END CDFSettings.makeWrapFilePreamble\n")
        f.close()

    def makeWrapFile(self):
        # super(CdfSettings,self).makeWrapFile()
        settings = self.settings
        wrapCommands = [
            "echo executing in directory",
            "pwd",
            """ if [ -e "$INPUT_TAR_FILE" ]; then echo untarring $INPUT_TAR_FILE; tar xvf "$INPUT_TAR_FILE" ; fi""",
            """export JOBSUB_USER_SCRIPT=%s    """ % settings[
                'exe_script'].replace('file://', ''),
            """echo executing: $JOBSUB_USER_SCRIPT "$@"   """,
            """$JOBSUB_USER_SCRIPT "$@"   """,
            "export JOB_RET_STATUS=$?",
        ]
        f = open(settings['wrapfile'], 'a')
        if settings['verbose']:
            f.write("###### BEGIN CDFSettings.makeWrapFile\n")
        self.writeToWrapFile(wrapCommands, f)
        if settings['verbose']:
            f.write("###### END CDFSettings.makeWrapFile\n")
        f.close()

    def makeWrapFilePostamble(self):
        settings = self.settings
        num_transfer_tries = settings.get('num_transfer_tries', '8')
        sleep_random = settings.get('sleep_random', '1800')
        postWrapCommands = [
            "cp ${JSB_TMP}/JOBSUB_LOG_FILE ./job_${CAF_SECTION}.out",
            "cp ${JSB_TMP}/JOBSUB_ERR_FILE ./job_${CAF_SECTION}.err",
            "tar cvzf ${OUTPUT_TAR_FILE} * ",
            """cpy_out="scp ${OUTPUT_TAR_FILE} ${OUTPUT_DESTINATION}"  """,
            """#num_tries and sleep_random are configurable in the jobsub.ini file""",
            """num_tries=%s""" % (num_transfer_tries),
            """sleep_random=%s""" % (sleep_random),
            """sleep_val=${CAF_SECTION}""",
            """cpy_stat=1""",
            """for itr in `seq $num_tries`""",
            """do""",
            """
            date
            echo sleeping $sleep_val seconds prior to copying to ${OUTPUT_DESTINATION}
            sleep $sleep_val
            date
            echo executing:$cpy_out
            $cpy_out
            cpy_stat=$?
            if [ $cpy_stat -eq 0 ]; then break; fi
            sleep_val=$((($RANDOM % $sleep_random)+1))
            date
            echo "$cpy_out failed on try $itr of $num_tries"
            """,
            """done""",
            """if [ "$cpy_stat" != "0" ]; then """,
            """  echo "$cpy_out failed, exiting with status $cpy_stat"  """,
            """  exit $cpy_stat""",
            """fi """
        ]
        f = open(settings['wrapfile'], 'a')
        if settings['verbose']:
            f.write("###### BEGIN CDFSettings.makeWrapFilePostamble\n")
        self.writeToWrapFile(postWrapCommands, f)
        if settings['verbose']:
            f.write("###### END CDFSettings.makeWrapFilePostmble\n")
        f.close()
        super(CdfSettings, self).makeWrapFilePostamble()

    def makeCommandFile(self, job_iter=0):
        settings = self.settings
        if job_iter > 0:
            tag = 'CAF_JOB_START_SECTION=([0-9]+)\;CAF_SECTION=([0-9]+)\;CAF_JOB_END_SECTION=([0-9]+)'
            x = settings['environment']
            y = re.sub(tag, "", x)
            this_section = job_iter + settings['firstSection'] - 1
            sect = "CAF_JOB_START_SECTION=%s;CAF_SECTION=%s;CAF_JOB_END_SECTION=%s" % (
                settings['firstSection'], this_section, settings['lastSection'])
            y2 = y + ";" + sect
            y = re.sub(";;", ";", y2)
            settings['environment'] = y
        super(CdfSettings, self).makeCommandFile(job_iter)

    def makeCondorFiles(self):
        settings = self.settings
        if 'SAM_GROUP' not in settings['added_environment']:
            settings['added_environment'].append('SAM_GROUP')
        if not os.environ.get('SAM_GROUP'):
            os.environ['SAM_GROUP'] = 'test'
        super(CdfSettings, self).makeCondorFiles()

    def checkSanity(self):
        settings = self.settings
        default_output_host = settings.get('default_output_host',
                                           'fcdflnxgpvm01.fnal.gov')
        if 'outLocation' not in settings:
            settings['outLocation'] = "%s@%s:%s_$.tgz" %\
                                      (settings['user'],
                                       default_output_host,
                                       settings['local_host'])
        if 'tar_file_name' not in settings:
            raise Exception(
                'you must supply an input tar ball using --tarFile')
        if 'sectionList' in settings:
            try:
                #print 'sectionList %s'%settings['sectionList']
                firstSection, lastSection = settings['sectionList'].split('-')
                #print 'first: %s last:%s'%(firstSection,lastSection)
                firstSection = int(firstSection)
                lastSection = int(lastSection)
                settings['firstSection'] = firstSection
                settings['lastSection'] = lastSection
                settings['queuecount'] = lastSection - firstSection + 1
                settings['job_count'] = lastSection - firstSection + 1
            except:
                err = "error, --sections='%s' must be of the form 'i-j' " %\
                    settings['sectionList']
                err += "where both i and j are positive integers"
                raise InitializationError(err)

        if 'lastSection' in settings:

            if settings['lastSection'] < 1:
                err = "--end value must be greater than 1"
                raise InitializationError(err)
        else:
            settings['lastSection'] = settings['queuecount']

        if 'firstSection' not in settings:
            settings['firstSection'] = 1

        numJobs = settings['lastSection'] - settings['firstSection'] + 1
        settings['queuecount'] = numJobs
        settings['job_count'] = numJobs

        if 'firstSection' in settings and 'lastSection' not in settings:
            err = 'you must specify a --end value if you specify a --start one'
            raise InitializationError(err)

        if 'firstSection' in settings and 'lastSection' in settings:
            if settings['lastSection'] < settings['firstSection']:
                err = " --end value must be greater than or equal to  --start value"
                raise InitializationError(err)
            elif settings['firstSection'] < 1:
                err = " --start value must be greater than or equal to 1"
                raise InitializationError(err)
            else:
                numJobs = settings['lastSection'] - \
                    settings['firstSection'] + 1
                settings['queuecount'] = numJobs
                settings['job_count'] = numJobs

        if 'firstSection' not in settings:
            settings['firstSection'] = 1
        if 'lastSection' not in settings:
            settings['lastSection'] = settings['queuecount']

        if 'job_count' not in settings:
            settings['job_count'] = settings['queuecount']

        return super(CdfSettings, self).checkSanity()
