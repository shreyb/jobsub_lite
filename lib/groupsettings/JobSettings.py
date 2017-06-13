#!/usr/bin/env python
# $Id$
import os
import sys
import datetime
import re
from JobUtils import JobUtils
from optparse import OptionParser
from optparse import OptionGroup
from JobsubConfigParser import JobsubConfigParser


class UnknownInputError(Exception):

    def __init__(self, errMsg="Unknown Input"):
        sys.exit(errMsg)
        Exception.__init__(self, errMsg)


class IllegalInputError(Exception):

    def __init__(self, errMsg="Illegal Input"):
        sys.exit(errMsg)
        Exception.__init__(self, errMsg)


class InitializationError(Exception):

    def __init__(self, errMsg="Initialization Error"):
        sys.exit(errMsg)
        Exception.__init__(self, errMsg)


class MyCmdParser(OptionParser):

    def print_help(self):
        OptionParser.print_help(self)
        # OptionParser.epilog doesn't work in v python 2.4, here is my
        # workaround
        epilog = """
        NOTES
        You can have as many instances of -c, -d, -e, -f, -l and -y as you need.

        The -d directory mapping works on non-Grid nodes, too.

        export IFDH_VERSION=some_version then use -e IFDH_VERSION to use
        the (some_version) release of ifdh for copying files in and out
        with -d and -f flags instead of the current ifdh version in KITS

        More documentation is available at
        https://cdcvs.fnal.gov/redmine/projects/jobsub/wiki/Using_the_Client
        address questions or problems to the service desk



                """
        print epilog


class JobSettings(object):

    def __init__(self):
        # print "JobSettings.__init__"

        if hasattr(self, 'cmdParser'):
            pass
        else:
            usage = "usage: %prog [options] your_script [your_script_args]\n"
            usage += "submit your_script to local batch or to the OSG grid "

            self.cmdParser = MyCmdParser(usage=usage,
                                         version=os.environ.get(
                                             "SETUP_JOBSUB_TOOLS", "NO_UPS_DIR"),
                                         conflict_handler="resolve")
            self.cmdParser.disable_interspersed_args()
            self.generic_group = OptionGroup(self.cmdParser, "Generic Options")
            self.cmdParser.add_option_group(self.generic_group)

            self.file_group = OptionGroup(self.cmdParser, "File Options")
            self.cmdParser.add_option_group(self.file_group)

            self.sam_group = OptionGroup(self.cmdParser, "SAM Options")
            self.cmdParser.add_option_group(self.sam_group)

        self.initFileParser()
        self.initCmdParser()
        self.settings = {}
        commands = JobUtils()
        (retVal, rslt) = commands.getstatusoutput("/bin/hostname")
        self.settings['local_host'] = rslt
        self.settings['submit_host'] = os.environ.get("SUBMIT_HOST")
        if self.settings['submit_host'] is None:
            self.settings['local_host'] = rslt
        self.settings['condor_tmp'] = os.environ.get("CONDOR_TMP", "/tmp")
        if self.settings['condor_tmp'] is None:
            raise InitializationError(
                "CONDOR_TMP not defined! setup_condor and try again")

        self.settings['condor_exec'] = os.environ.get("CONDOR_EXEC", "/tmp")
        self.settings['condor_config'] = os.environ.get("CONDOR_CONFIG")
        self.settings['local_condor'] = os.environ.get(
            "LOCAL_CONDOR", "/opt/condor/bin")
        self.settings['group_condor'] = os.environ.get(
            "GROUP_CONDOR", "/this/is/bogus")

        self.settings['x509_user_proxy'] = os.environ.get("X509_USER_PROXY")
        if self.settings['x509_user_proxy'] is None:
            user = os.environ.get("USER")
            group = os.environ.get("GROUP", "common")
            if group == "common":
                self.settings[
                    'x509_user_proxy'] = "/scratch/%s/grid/%s.proxy" % (user, user)
            else:
                self.settings[
                    'x509_user_proxy'] = "/scratch/%s/grid/%s.%s.proxy" % (user, user, group)

        self.settings['ifdh_base_uri'] = os.environ.get("IFDH_BASE_URI")
        if self.settings['ifdh_base_uri'] is None:
            group = os.environ.get("GROUP", "common")
            self.settings[
                'ifdh_base_uri'] = "http://samweb.fnal.gov:8480/sam/%s/api" % (group)

        self.settings['output_tag_array'] = {}
        self.settings['input_dir_array'] = []
        self.settings['output_dir_array'] = []

        self.settings['istestjob'] = False
        self.settings['needafs'] = False
        self.settings['notify'] = 1
        self.settings['submit'] = True
        self.settings['grid'] = False

        self.settings['usepwd'] = True
        self.settings['forceparrot'] = False
        self.settings['forcenoparrot'] = True
        self.settings['useparrot'] = False
        self.settings['usedagman'] = False
        self.settings[
            'requirements'] = '((target.Arch==\"X86_64\") || (target.Arch==\"INTEL\"))'
        fmt_str = 'CLUSTER=%s;PROCESS=%s;DAGMANJOBID=%s'
        self.settings['environment'] = fmt_str % ('$(Cluster)',
                                                  '$(Process)',
                                                  '$(DAGManJobId)')
        self.settings['lines'] = []
        self.settings['group'] = os.environ.get("GROUP", "common")
        self.settings['storage_group'] = os.environ.get("STORAGE_GROUP")
        self.settings['accountinggroup'] = self.settings['group']
        self.settings['user'] = os.environ.get("USER")
        self.settings['version'] = os.environ.get(
            "SETUP_JOBSUB_TOOLS", "NO_UPS_VERSION")
        self.settings['output_tag_counter'] = 0
        self.settings['input_tag_counter'] = 0
        self.settings['queuecount'] = 1
        self.settings['joblogfile'] = ""
        self.settings['override_x509'] = False
        self.settings['use_gftp'] = False
        self.settings['filebase'] = ''
        self.settings['filetag'] = ''
        self.settings['wrapfile'] = ''
        self.settings['parrotfile'] = ''
        self.settings['cmdfile'] = ''
        self.settings['dagfile'] = ''
        self.settings['dagbeginfile'] = ''
        self.settings['dagendfile'] = ''
        self.settings['processtag'] = ''
        self.settings['logfile'] = ''
        self.settings['opportunistic'] = False
        self.settings['nowrapfile'] = False
        self.settings['errfile'] = ''
        self.settings['outfile'] = ''
        self.settings['exe_script'] = ''
        self.settings['script_args'] = []
        self.settings['verbose'] = False
        self.settings['nologbuffer'] = False
        self.settings['wrapper_cmd_array'] = []
        self.settings['msopt'] = ""
        self.settings['added_environment'] = []
        self.settings['generated_by'] = "%s %s" % (
            self.settings['version'], self.settings['local_host'])
        self.settings['input_tar_dir'] = False
        self.settings['tar_file_name'] = ""
        self.settings['overwrite_tar_file'] = False
        self.settings['site'] = False
        self.settings['dataset_definition'] = ""
        self.settings['project_name'] = ""
        self.settings['cmd_file_list'] = []
        self.settings['jobsub_tools_dir'] = os.environ.get(
            "JOBSUB_TOOLS_DIR", "/tmp")
        self.settings['ups_shell'] = os.environ.get("UPS_SHELL")
        #self.settings['condor_setup_cmd']='. /opt/condor/condor.sh; '
        self.settings[
            'downtime_file'] = '/grid/fermiapp/common/jobsub_MOTD/JOBSUB_UNAVAILABLE'
        self.settings['motd_file'] = '/grid/fermiapp/common/jobsub_MOTD/MOTD'
        self.settings['wn_ifdh_location'] = os.environ.get(
            "WN_IFDH_LOCATION", '/grid/fermiapp/products/common/etc/setups.sh')
        self.settings['desired_os'] = ''
        self.settings['default_grid_site'] = False
        self.settings['resource_list'] = []
        self.settings['transfer_executable'] = False
        self.settings['transfer_input_files'] = os.environ.get(
            "TRANSFER_INPUT_FILES", "")
        self.settings['needs_appending'] = True
        self.settings['ifdh_cmd'] = '${JSB_TMP}/ifdh.sh'
        self.settings['jobsub_max_joblog_size'] = 5000000
        self.settings['drain'] = False
        self.settings['mail_domain'] = 'fnal.gov'
        if not self.settings.get('schedd'):
            self.settings['schedd'] = self.settings['submit_host']
        self.settings['jobsubjobid'] = "$(CLUSTER).$(PROCESS)@%s" % self.settings[
            'schedd']
        schedd_host = self.settings.get('schedd').split('@')[-1]
        if schedd_host != self.settings['submit_host']:
            self.settings['local_schedd'] = False
        else:
            self.settings['local_schedd'] = True

        (stat, jobsub) = commands.getstatusoutput("which jobsub")
        self.settings['mail_summary'] = False
        self.settings['this_script'] = jobsub
        self.settings[
            'summary_script'] = "%s/summary.sh" % (os.path.dirname(self.settings['this_script']))
        self.settings[
            'dummy_script'] = "%s/returnOK.sh" % (os.path.dirname(self.settings['this_script']))
        self.settings['subgroup'] = None
        self.settings['jobsub_max_cluster_procs'] = 10000
        self.settings['job_expected_max_lifetime'] = 21600
        self.settings['set_expected_max_lifetime'] = None

        # for w in sorted(self.settings,key=self.settings.get,reverse=True):
        #        print "%s : %s"%(w,self.settings[w])
        # sys.exit

    def runCmdParser(self, a=None, b=None):
        (options, args) = self.cmdParser.parse_args(a, b)

        self.runFileParser()
        new_settings = vars(options)
        if 'verbose' in new_settings and new_settings['verbose']:
            print "new_settings = ", new_settings
        for x in new_settings.keys():
            if new_settings[x] is not None:
                self.settings[x] = new_settings[x]
        settings = self.settings
        # for w in sorted(self.settings,key=self.settings.get,reverse=True):
        #        print "%s : %s"%(w,self.settings[w])
        # sys.exit
        if 'override' in new_settings:
            (a, b) = new_settings['override']
            self.settings[a] = b

        if(len(args) < 1):
            print "error, you must supply a script to run"
            print "jobsub -h for help"
            sys.exit(1)
        self.settings['exe_script'] = args[0]
        executable_ok = os.access(self.settings['exe_script'], os.X_OK)
        if not executable_ok and os.path.exists(self.settings['exe_script']):
            os.chmod(self.settings['exe_script'], 0o775)

        # yuck
        if(len(args) > 1):
            self.settings['script_args'] = args[1:]
        for x in settings.keys():
            if settings[x] in ['True', 'true', 'TRUE']:
                settings[x] = True
            if settings[x] in ['False', 'false', 'FALSE']:
                settings[x] = False
        if 'transfer_wrapfile' in settings:
            settings['tranfer_executable'] = settings['transfer_wrapfile']
        if 'always_run_on_grid' in settings and settings['always_run_on_grid']:
            settings['grid'] = True
        if settings['tar_file_name']:
            settings['tar_file_basename'] = os.path.basename(
                settings['tar_file_name'])

    def findConfigFile(self):
        if 'jobsub_ini_file' in self.settings:
            cnf = self.settings['jobsub_ini_file']
        else:
            cnf = self.fileParser.findConfigFile()
            self.settings['jobsub_ini_file'] = cnf
        return cnf

    def runFileParser(self):
        grp = os.environ.get("GROUP")
        commands = JobUtils()
        pairs = []
        if grp is None:
            (stat, grp) = commands.getstatusoutput("id -gn")
            user = os.environ.get("USER", "fermilab")
        exps = self.fileParser.sections()
        if grp not in exps:
            grp = "fermilab"
        if self.fileParser.has_section('default'):
            pairs.extend(self.fileParser.items('default'))
        if self.fileParser.has_section(grp):
            pairs.extend(self.fileParser.items(grp))
        sbhst = os.environ.get("SUBMIT_HOST")
        if sbhst is None:
            sbhst = self.settings['submit_host']
        if self.fileParser.has_section(sbhst):
            pairs.extend(self.fileParser.items(sbhst))
        use_these = dict(pairs)
        for (x, y) in pairs:
            eval = os.environ.get(x.upper(), None)
            if eval is not None:
                self.settings[x] = eval
            else:
                yp = use_these[x]
                cmd = "echo %s" % yp
                (stat, rslt) = commands.getstatusoutput(cmd)
                self.settings[x] = rslt

    def schedd_callback(self, option, opt, value, p):
        # print "callback opt=%s val=%s"%(opt,value)
        self.settings['jobsubjobid']="$(CLUSTER).$(PROCESS)@%s"% value
        self.settings['schedd']= value

    def resource_callback(self, option, opt, value, p):
        # print "callback opt=%s val=%s"%(opt,value)
        self.settings['resource_list'].append(value)

    def initFileParser(self):
        self.fileParser = JobsubConfigParser()

    def initCmdParser(self):
        """Initialize the groups in the cmdParser
        """

        generic_group = self.generic_group
        file_group = self.file_group
        sam_group = self.sam_group

        file_group.add_option("-l", "--lines", dest="lines", action="append",
                              type="string", metavar='"line"',
                              help=' '.join(["""[Expert option]  Add  "line" to the Condor """,
                                             """submission (.cmd) file, typically as a classad attribute.  """,
                                             """See the HTCondor documentation  for more."""]))

        generic_group.add_option("--timeout", dest="timeout", action="store",
                                 type="string", metavar='NUMBER[UNITS]',
                                 help=' '.join(["""kill user job if still running after NUMBER[UNITS] of time .""",
                                                """UNITS may be `s' for seconds (the default), `m' for minutes,""",
                                                """`h' for hours or `d' h for days."""]))

        submit_host = os.environ.get('SUBMIT_HOST')
        ex_short = self.fileParser.get(
            submit_host, 'job_expected_max_lifetime_short')
        ex_med = self.fileParser.get(
            submit_host, 'job_expected_max_lifetime_medium')
        ex_long = self.fileParser.get(
            submit_host, 'job_expected_max_lifetime_long')
        ex_default = self.fileParser.get(
            submit_host, 'job_expected_max_lifetime_default')

        generic_group.add_option("--expected-lifetime", dest="set_expected_max_lifetime", action="store",
                                 type="string", metavar="'short'|'medium'|'long'|NUMBER[UNITS]",
                                 help=' '.join(["""Expected lifetime of the job.  Used to match against""",
                                                """resources advertising that they have REMAINING_LIFETIME seconds left.  The shorter your""",
                                                """EXPECTED_LIFTIME is, the more resources (aka slots, cpus) your job can potentially""",
                                                """match against and the quicker it should start.  If your job runs longer than """,
                                                """EXPECTED_LIFETIME it *may* be killed by the batch system.  If your specified """,
                                                """EXPECTED_LIFETIME is too long your job may take a long time to match against """,
                                                """a resource a sufficiently long REMAINING_LIFETIME.  Valid inputs for this parameter""",
                                                """are 'short', 'medium', 'long', or NUMBER[UNITS] of time.  IF [UNITS] is omitted, value is NUMBER  seconds.""",
                                                """Allowed values for UNITS are 's', 'm', 'h', 'd' representing seconds, minutes, etc."""
                                                """The values for 'short','medium',and 'long' are configurable by Grid Operations, they currently""",
                                                """are '%s' , '%s' , and '%s' but this may change in the future.""" % (
                                                    ex_short, ex_med, ex_long),
                                                """Default value of  EXPECTED_LIFETIME is currently '%s' .""" % (ex_default) ]))

        generic_group.add_option("--maxConcurrent",
                                 dest="maxConcurrent",
                                 action="store", type="string",
                                 help=re.sub('  \s+', ' ', """
        max number of jobs running concurrently at given time. Use in
        conjunction with -N option to protect a shared resource.
        Example: jobsub -N 1000 -maxConcurrent 20 will
        only run 20 jobs at a time until all 1000 have completed.
        This is implemented by running the jobs in a DAG. Normally when
        jobs are run with the -N option, they all have the same $CLUSTER
        number and differing, sequential $PROCESS numbers, and many submission
        scripts take advantage of this.  When jobs are run with this
        option in a DAG each job has a different $CLUSTER number and a
        $PROCESS number of 0, which may break scripts that rely on the
        normal -N numbering scheme for $CLUSTER and $PROCESS. Groups of
        jobs run with this option will have the same $JOBSUBPARENTJOBID,
        each individual job will have a unique and sequential
        $JOBSUBJOBSECTION.
        Scripts may need modification to take this into account"""))

        generic_group.add_option("--disk", dest="disk", metavar="NUMBER[UNITS]",
                                 action="store", type="string",
                                 help=' '.join(["""Request worker nodes have at least NUMBER[UNITS] of disk space.   """,
                                                """If UNITS is not specified default is 'KB' (a typo in earlier versions """,
                                                """said that default was 'MB', this was wrong).  Allowed values for """,
                                                """UNITS are 'KB','MB','GB', and 'TB'"""]))

        generic_group.add_option("--memory", dest="memory",
                                 metavar="NUMBER[UNITS]",
                                 action="store", type="string",
                                 help=re.sub('  \s+', ' ', """
                Request worker nodes have at least NUMBER[UNITS]  of memory.
                If UNITS is not specified default is 'MB'.   Allowed values for
                UNITS are 'KB','MB','GB', and 'TB' """))

        generic_group.add_option("--cpu", dest="cpu", metavar="NUMBER",
                                 action="store", type="int",
                                 help=re.sub('  \s+', ' ', """
                        request worker nodes have at least NUMBER cpus """))

        sam_group.add_option("--dataset_definition", dest="dataset_definition",
                             action="store", type="string",
                             help=re.sub('  \s+', ' ', """
                SAM dataset definition used in a Directed Acyclic Graph (DAG)
                """))

        sam_group.add_option("--project_name", dest="project_name",
                             action="store", type="string",
                             help="optional project name for SAM DAG ")

        generic_group.add_option("--drain", dest="drain",
                                 action="store_true",
                                 help=re.sub('  \s+', ' ', """
                mark this job to be allowed to be drained or killed during
                downtimes """))

        generic_group.add_option("--schedd", dest="schedd",
                                 action="callback", type="string",callback=self.schedd_callback,
                                 help="name of alternate schedd to submit to")

        generic_group.add_option("--OS", dest="os",
                                 action="store", type="string",
                                 help=re.sub('  \s+', ' ', """
                specify OS version of worker node. Example
                --OS=SL5  Comma seperated list
                '--OS=SL4,SL5,SL6' works as well . Default is any available OS
                """))

        generic_group.add_option("--show-parsing", dest="show_parsing",
                                 action="store_true", default=False,
                                 help=re.sub('  \s+', ' ', """
                print out how command line was parsed into argv
                list and exit.
                Useful for seeing how quotes in options are parsed)"""))

        generic_group.add_option("--generate-email-summary",
                                 dest="mail_summary",
                                 action="store_true", default=False,
                                 help=re.sub('  \s+', ' ', """
                generate and mail a summary report of completed/failed/removed
                jobs in a DAG"""))

        generic_group.add_option("--email-to", dest="notify_user",
                                 action="store", type="string",
                                 help=re.sub('  \s+', ' ', """
                email address to send job reports/summaries to
                (default is $USER@fnal.gov)"""))

        generic_group.add_option("-G", "--group", dest="accountinggroup",
                                 action="store", type="string",
                                 help=re.sub('  \s+', ' ', """
                Group/Experiment for priorities and accounting"""))

        generic_group.add_option("--subgroup", dest="subgroup",
                                 action="store", type="string",
                                 help=re.sub('  \s+', ' ', """
                Subgroup for priorities and accounting. See
                https://cdcvs.fnal.gov/redmine/projects/jobsub/wiki/
                Jobsub_submit#Groups-Subgroups-Quotas-Priorities
                for more documentation on using --subgroup to set job
                quotas and priorities"""))

        generic_group.add_option("-v", "--verbose", dest="verbose",
                                 action="store_true", default=False,
                                 help=re.sub('  \s+', ' ', """
                dump internal state of program (useful for debugging)"""))

        generic_group.add_option("--resource-provides", type="string",
                                 action="callback",
                                 callback=self.resource_callback,
                                 help=re.sub('  \s+', ' ', """request specific
                                 resources by changing condor jdf file.
                                 For example: --resource-provides=CVMFS=OSG
                                 will add +CVMFS=\"OSG\" to the job classad
                                 attributes and '&&(CVMFS==\"OSG\")' to the
                                 job requirements"""))

        generic_group.add_option("-M", "--mail_always", dest="notify",
                                 action="store_const", const=2,
                                 help="send mail when job completes or fails")

        generic_group.add_option("-q", "--mail_on_error", dest="notify",
                                 action="store_const", const=1,
                                 help=re.sub('  \s+', ' ', """send mail only
                                 when job fails due to error (default)"""))

        generic_group.add_option("-Q", "--mail_never", dest="notify",
                                 action="store_const", const=0,
                                 help=re.sub('  \s+', ' ', """
                    never send mail (default is to send mail on error)"""))

        # generic_group.add_option("-T","--test_queue", dest="istestjob",
        #    action="store_true",default=False,
        #    help="""Submit as a test job.  Job will run with highest
        #    possible priority, but you can only have one such
        #    job in the queue at a time.""")

        file_group.add_option("-L", "--log_file", dest="joblogfile",
                              action="store",
                              help="Log file to hold log output from job.")

        file_group.add_option("--compress_log", dest="compress_log",
                              action="store_true",
                              default=False,
                              help="Compress --log_file output .")

        file_group.add_option("--no_log_buffer", dest="nologbuffer",
                              action="store_true",
                              help=re.sub('  \s+', ' ', """write log file
            directly to disk. DOES NOT WORK WITH PNFS, WILL NOT WORK WITH
            BLUEARC WHEN IT IS UNMOUNTED FROM WORKER NODES VERY SOON.
            Default is to copy it back after job is completed.
            This option is useful for debugging but can be VERY DANGEROUS as
            joblogfile typically is sent to bluearc.  Using this option
            incorrectly can cause all grid submission systems at FNAL to
            become overwhelmed resulting in angry admins hunting you down, so
            USE SPARINGLY. """))

        generic_group.add_option("-g", "--grid", dest="grid",
                                 action="store_true",
                                 help=re.sub('  \s+', ' ', """run job on the
            FNAL GP  grid. Other flags can modify target sites to include other
            areas of the Open Science Grid"""))

        generic_group.add_option("--nowrapfile", dest="nowrapfilex",
                                 action="store_true",
                                 help=re.sub('  \s+', ' ', """DISABLED:
            formerly was 'do not generate shell wrapper, disabled per request
            from fermigrid operations.  The wrapfiles used to not  work off
            site, now they do.""") )

        file_group.add_option("--use_gftp", dest="use_gftp",
                              action="store_true", default=False,
                              help="use grid-ftp to transfer file back")

        generic_group.add_option("-c", "--append_condor_requirements",
                                 dest="append_requirements", action="append",
                                 help="append condor requirements")

        generic_group.add_option("--overwrite_condor_requirements",
                                 dest="overwriterequirements", action="store",
                                 help=re.sub('  \s+', ' ', """overwrite default
                                 condor requirements with supplied
                                 requirements"""))

        generic_group.add_option("--override", dest="override", nargs=2,
                                 action="store", default=(1, 1),
                                 help=re.sub('  \s+', ' ', """override some
            other value: --override 'requirements' 'gack==TRUE' would produce
            the same condor command file as --overwrite_condor_requirements
            'gack==TRUE' if you want to use this option, test it first with -n
            to see what you get as output """))

        generic_group.add_option("-C", dest="usepwd", action="store_true",
                                 default=False,
                                 help=re.sub('  \s+', ' ', """execute on
                                 grid from directory you are currently in
                                 NOTE:WILL STOP WORKING SOON WHEN BLUARC
                                 UNMOUNTED FROM WORKER NODES
                                 """))

        generic_group.add_option("-e", "--environment",
                                 dest="added_environment", action="append",
                                 metavar='ENV_VAR',
                                 help=re.sub('  \s+', ' ', """-e
        ADDED_ENVIRONMENT exports this variable with its local
        value to worker node environment. For example export FOO="BAR";
        jobsub -e FOO <more stuff> guarantees that the value of $FOO on
        the worker node is "BAR" .  Alternate format which does not require
        setting the env var first is the -e VAR=VAL, idiom which
        sets the value of $VAR to 'VAL' in the worker environment. The
        -e  option can be used as many times in one jobsub_submit
        invocation as desired"""))

        generic_group.add_option("--site", dest="site", action="store",
                                 metavar='COMMA,SEP,LIST,OF,SITES',
                                 help="submit jobs to these sites ")

        generic_group.add_option("--blacklist", dest="blacklist", action="store",
                                 metavar='COMMA,SEP,LIST,OF,SITES',
                                 help="ensure that jobs do not land at these sites ")

        file_group.add_option("--tar_file_name", dest="tar_file_name",
                              action="store",
                              metavar="dropbox://PATH/TO/TAR_FILE",
                              help=re.sub('  \s+', ' ', """specify tarball
                    to transfer to worker node. TAR_FILE
                    will be copied to the jobsub server and added to the
                    transfer_input_files list. TAR_FILE will be accessible
                    to the user job on the worker node via the environment
                    variable  $INPUT_TAR_FILE.  """))

        generic_group.add_option("-n", "--no_submit", dest="submit",
                                 action="store_false", default=True,
                                 help=re.sub('  \s+', ' ', """generate
                                 condor_command file but do not submit"""))

        generic_group.add_option("-N", dest="queuecount", metavar='NUM',
                                 action="store",
                                 default=1, type="int",
                                 help=re.sub('  \s+', ' ', """submit N copies
            of this job. Each job will
            have access to the environment variable
            $PROCESS that provides the job number (0 to
            NUM-1), equivalent to the number following the decimal point in
            the job ID (the '2' in 134567.2). """))

        file_group.add_option("-f", dest="input_dir_array", action="append",
                              type="string", metavar='INPUT_FILE',
                              help=re.sub('  \s+', ' ',
                                          """at runtime, INPUT_FILE will be copied to directory
            $CONDOR_DIR_INPUT on the execution node.
            Example :-f /grid/data/minerva/my/input/file.xxx
            will be copied to $CONDOR_DIR_INPUT/file.xxx
            Specify as many -f INPUT_FILE_1 -f INPUT_FILE_2
            args as you need.  To copy file at submission time
            instead of run time, use -f dropbox://INPUT_FILE to
            copy the file. """))

        file_group.add_option("-d", dest="output_dir_array",
                              action="append", type="string",
                              nargs=2,
                              help=re.sub('  \s+', ' ', """
            -d<tag> <dir>  Writable directory $CONDOR_DIR_<tag> will
            exist on the execution node.  After job completion,
            its contents will be moved to <dir> automatically
            Specify as many <tag>/<dir> pairs as you need. """))

    def expectedLifetimeOK(self, a_str):
        if 'lines' in self.settings:
            for line in self.settings['lines']:
                if line.startswith("+JOB_EXPECTED_MAX_LIFETIME"):
                    return True
        try:
            i = int(a_str)
            self.settings['job_expected_max_lifetime'] = i
            self.addToLineSetting("+JOB_EXPECTED_MAX_LIFETIME = %s" % i)
            print "Warning: --expected-lifetime=%s had no units! Valid units are 's','m','h','d'. Assuming seconds" % a_str
            return True
        except ValueError:
            try:
                units = a_str.lower()
                if units in ['short', 'medium', 'long']:
                    key = 'job_expected_max_lifetime_%s' % units
                    val = self.settings.get(key, None)
                    # if val:
                    #    self.settings['job_expected_max_lifetime'] = val
                    #    self.addToLineSetting("+JOB_EXPECTED_MAX_LIFETIME = %s"%val)
                    #    return True
                    return self.expectedLifetimeOK(val)

                elif units[-1] in ['s', 'm', 'h', 'd']:
                    try:
                        i = int(units[:-1])
                    except ValueError:
                        print " --expected-lifetime='%s' not valid input" % a_str
                        return False
                    if units[-1] == 's':
                        val = i
                    elif units[-1] == 'm':
                        val = i * 60
                    elif units[-1] == 'h':
                        val = i * 60 * 60
                    elif units[-1] == 'd':
                        val = i * 60 * 60 * 24
                    self.addToLineSetting(
                        "+JOB_EXPECTED_MAX_LIFETIME = %s" % val)
                    return True
                else:
                    return False
            except:
                return False

    def timeFormatOK(self, a_str):
        try:
            i = int(a_str)
            print "Warning: --timeout=%s had no units! Valid units are 's','m','h','d'. Assuming seconds" % a_str
            return True
        except ValueError:
            try:
                units = a_str[-1]
                if units in ['s', 'm', 'h', 'd']:
                    return True
                else:
                    return False
            except:
                return False

    def diskFormatOK(self, a_str):
        try:
            i = int(a_str)
            print "Warning: --disk=%s had no units! Valid units are 'KB','MB','GB','TB'.  Assuming KB" % a_str
            return True
        except ValueError:
            try:
                units = a_str[-2:].upper()
                if units in ['KB', 'MB', 'GB', 'TB']:
                    return True
                else:
                    return False
            except:
                return False

    def memFormatOK(self, a_str):
        try:
            i = int(a_str)
            print "Warning: --memory=%s had no units! Valid units are 'KB','MB','GB','TB'.  Assuming MB" % a_str
            return True
        except ValueError:
            try:
                units = a_str[-2:].upper()
                if units in ['KB', 'MB', 'GB', 'TB']:
                    return True
                else:
                    return False
            except:
                return False

    def checkSanity(self):
        settings = self.settings
        for i, arg in enumerate(settings['added_environment']):
            if '=' in arg or (arg in os.environ) == False:
                if (arg in os.environ) == False and '=' not in arg:
                    err = "you used -e %s , but $%s must be set first for this to work!" % (
                        arg, arg)
                    raise InitializationError(err)
                elif '=' in arg:
                    try:
                        a, b = arg.split('=')
                        if len(a) < 1:
                            raise InitializationError(
                                "error processing -e %s" % arg)
                        os.environ[a] = b
                        settings['added_environment'].pop(i)
                        settings['added_environment'].insert(i, a)
                    except:
                        raise InitializationError(
                            "error processing -e %s" % arg)
                else:
                    err = 'error setting up running environment'
                    raise InitializationError(err)

        if settings.get('memory') and not self.memFormatOK(settings['memory']):
            err = "--memory '%s' format incorrect" % settings['memory']
            raise InitializationError(err)

        if settings.get('disk') and not self.diskFormatOK(settings['disk']):
            err = "--disk '%s' format incorrect" % settings['disk']
            raise InitializationError(err)

        if settings.get('timeout') and not self.timeFormatOK(
                settings['timeout']):
            err = "--timeout '%s' format incorrect" % settings['timeout']
            raise InitializationError(err)

        if settings.get('set_expected_max_lifetime'):
            if not self.expectedLifetimeOK(
                    settings['set_expected_max_lifetime']):
                err = "--expected-lifetime '%s' format incorrect" % settings[
                    'set_expected_max_lifetime']
                raise InitializationError(err)
        else:
            default_lifetime = settings.get(
                'job_expected_max_lifetime_default')
            if not default_lifetime:
                default_lifetime = 6 * 60 * 60
            if not self.expectedLifetimeOK(default_lifetime):
                err = 'default lifetime="%s" is not allowed' % default_lifetime
                raise InitializationError(err)

        if int(settings['queuecount']) < 1:
            err = "-N  must be a positive number"
            raise InitializationError(err)

        if int(settings['queuecount']) > int(
                settings['jobsub_max_cluster_procs']):
            err = "-N was set to %s , cannot be greater than %s " % (
                settings['queuecount'], settings['jobsub_max_cluster_procs'])
            raise InitializationError(err)

        if settings['istestjob'] and settings['queuecount'] > 1:
            err = "you may only send one test job at a time, -N=%d not allowed" % settings[
                'queuecount']
            raise InitializationError(err)

        # if settings['nologbuffer'] and settings['queuecount'] > 1:
            #err = " --nologbuffer and -N=%d (where N>1) options are not allowed together " % settings['queuecount']
            #raise InitializationError(err)

        if settings['nologbuffer'] and settings['use_gftp']:
            err = " --use_gftp and --no_log_buffer together make no sense"
            raise InitializationError(err)

        if settings['nologbuffer'] and settings['joblogfile'] == "":
            err = "you must specify an input value for the log file with -L if you use --no_log_buffer"
            raise InitializationError(err)

        if 'compress_log' in settings and 'joblogfile' not in settings:
            err = "you must specify an input value for the log file with -L if you use --compress_log"
            raise InitializationError(err)

        if settings['input_tar_dir'] and settings['tar_file_name'] == "":
            err = "you must specify a --tar_file_name if you create a tar file using --input_tar_dir"
            raise InitializationError(err)

        if settings.get('site') and settings.get('blacklist'):
            siteset = set(settings.get('site').split(','))
            blset = set(settings.get('blacklist').split(','))
            intset = siteset & blset
            if intset:
                err = 'There are common sites in both --site and --blacklist %s your jobs will never start' % intset
                raise InitializationError(err)


        if 'nowrapfilex' in settings and settings['nowrapfilex']:
            print """WARNING the --nowrapfile option has been disabled at the request of
            the Grid Operations group.  Your jobs will be submitted with a wrapper and should still
            run normally. If they do not please open a service desk ticket
             """
            settings['nowrapfilex'] = False

        if settings['dataset_definition'] != "":
            settings['usedagman'] = True

        if 'maxConcurrent' in settings and settings['maxConcurrent'] != "":
            settings['usedagman'] = True

        if settings['usedagman']:
            settings['jobsubparentjobid'] = "$(DAGManJobId).0@%s" % settings[
                'schedd']
            self.addToLineSetting(
                """+JobsubParentJobId = "%s" """ % settings['jobsubparentjobid'])

        return True

    def makeParrotFile(self):
        raise Exception(
            "parrot file generation has been turned off.  Please report this error to the service desk")
        # print "makeParrotFile"

    def makeWrapFilePreamble(self):
        """ Make beginning part of wrapfile. ($CONDOR_TMP/user_job_(numbers)_wrap.sh  Change env
            variables so that default behavior is for condor generated files NOT to come back to
            submit host, handle ifdh transfer of input files """

        settings = self.settings
        f = open(settings['wrapfile'], 'a')
        if settings['verbose']:
            f.write("#!/bin/sh -x \n")
        else:
            f.write("#!/bin/sh\n")
        f.write("#\n")
        if settings['verbose']:
            f.write("\n########BEGIN JOBSETTINGS makeWrapFilePreamble#############\n")
        f.write("umask 002\n")
        f.write("# %s\n" % settings['wrapfile'])
        f.write("# Automatically generated by: \n")
        ln = int(len(sys.argv))
        f.write("#          %s %s \n" %
                (os.path.basename(sys.argv[0]), " ".join(sys.argv[1:])))

        f.write("\n")
        f.write("%s\n" % JobUtils().logTruncateString())
        ifdh_pgm_text = JobUtils().ifdhString() % (settings['ifdh_cmd'], settings[
            'wn_ifdh_location'], settings['ifdh_cmd'])
        f.write(ifdh_pgm_text)
        f.write("\n")
        f.write(
            "\n#########################################################################\n")
        f.write(
            "# main ()                                                               #\n")
        f.write(
            "#########################################################################\n")
        f.write("touch .empty_file\n")
        if 'tar_file_basename' in settings:
            f.write(
                "export INPUT_TAR_FILE=${_CONDOR_JOB_IWD}/%s\n" % settings['tar_file_basename'])
            # this is not the right way to do this, should look at ini file to see where to
            # untar it or whether to untar it at all
            # doing it this way now as we need to get this out the door
            if settings['group'] != 'cdf':
                f.write(
                    """if [ -e "$INPUT_TAR_FILE" ]; then tar xvf "$INPUT_TAR_FILE" ; fi\n""")

        f.write("# Hold and clear arg list\n")
        f.write("args=\"$@\"\n")
        f.write("set - \"\"\n")
        f.write("""[[ "$JOBSUB_DEBUG" ]] && set_jobsub_debug\n""")
        f.write("\n")
        f.write("export JSB_TMP=$_CONDOR_SCRATCH_DIR/jsb_tmp\n")
        f.write("mkdir -p $JSB_TMP\n")
        f.write("export _CONDOR_SCRATCH_DIR=$_CONDOR_SCRATCH_DIR/no_xfer\n")
        f.write("export TMP=$_CONDOR_SCRATCH_DIR\n")
        f.write("export TEMP=$_CONDOR_SCRATCH_DIR\n")
        f.write("export TMPDIR=$_CONDOR_SCRATCH_DIR\n")
        f.write("mkdir -p $_CONDOR_SCRATCH_DIR\n")
        #f.write("""if [ "${JOBSUB_MAX_JOBLOG_SIZE}" = "" ] ; then JOBSUB_MAX_JOBLOG_SIZE=%s ; fi \n"""%settings['jobsub_max_joblog_size'])
        # if settings.has_key('jobsub_max_joblog_tail_size'):
        # f.write("""JOBSUB_MAX_JOBLOG_TAIL_SIZE=%s\n"""%settings['jobsub_max_joblog_tail_size'])
        # if settings.has_key('jobsub_max_joblog_head_size'):
        # f.write("""JOBSUB_MAX_JOBLOG_HEAD_SIZE=%s\n"""%settings['jobsub_max_joblog_head_size'])
        f.write("""redirect_output_start\n""")

        f.write("\n")
        f.write(JobUtils().krb5ccNameString())
        f.write("\n")
        f.write("setup_ifdh_env\n")
        if 'set_up_ifdh' in settings and settings['set_up_ifdh']:
            f.write("\nsource ${JSB_TMP}/ifdh.sh > /dev/null\n")

        f.close()
        self.wrapFileCopyInput()
        if settings['verbose']:
            f = open(settings['wrapfile'], 'a')
            f.write("########END JOBSETTINGS makeWrapFilePreamble#############\n")
            f.close()

    def makeWrapFile(self):
        """ Make middle part of wrapfile ($CONDOR_TMP/user_job_(numbers)_wrap.sh . Execute
        user job, capture exit status, report this info back via ifdh log
        """

        settings = self.settings
        f = open(settings['wrapfile'], 'a')
        tlimit = ''
        if settings.get('timeout'):
            tlimit = "timeout %s " % settings['timeout']

        ifdh_cmd = settings['ifdh_cmd']
        exe_script = settings['exe_script']
        if settings['transfer_executable']:
            exe_script = os.path.basename(settings['exe_script'])
        f.write("export JOBSUB_EXE_SCRIPT=`find . -name %s -print`\n" %
                os.path.basename(settings['exe_script']))
        f.write("chmod +x $JOBSUB_EXE_SCRIPT\n")
        script_args = ''
        if settings['verbose']:
            f.write("########BEGIN JOBSETTINGS makeWrapFile #############\n")
        for x in settings['script_args']:
            script_args = script_args + x + " "
        log_msg = """BEGIN EXECUTION $JOBSUB_EXE_SCRIPT  %s \n""" % (
            script_args)
        log_cmd = """%s log "%s:%s "\n""" %\
            (ifdh_cmd, settings['user'], log_msg)
        f.write(log_cmd)
        f.write("%s\n" % JobUtils().poms_info())
        f.write("""%s log poms_data=$poms_data\n""" % ifdh_cmd)
        f.write("echo `date` %s" % log_msg)
        f.write(">&2 echo `date` %s" % log_msg)
        if settings['joblogfile'] != "":
            if settings['nologbuffer'] == False:
                f.write("%s$JOBSUB_EXE_SCRIPT %s > $_CONDOR_SCRATCH_DIR/tmp_job_log_file 2>&1\n" %
                        (tlimit, script_args))
            else:
                f.write("%s$JOBSUB_EXE_SCRIPT %s > %s  2>&1\n" %
                        (tlimit, script_args, settings['joblogfile']))

        else:
            f.write("%s$JOBSUB_EXE_SCRIPT %s  \n" %
                    (tlimit, script_args))

        f.write("JOB_RET_STATUS=$?\n")
        f.write(
            "echo `date` $JOBSUB_EXE_SCRIPT COMPLETED with exit status $JOB_RET_STATUS\n")
        f.write(
            "echo `date` $JOBSUB_EXE_SCRIPT COMPLETED with exit status $JOB_RET_STATUS 1>&2\n")

        log_cmd = """%s log "%s:%s COMPLETED with return code $JOB_RET_STATUS" \n""" % \
            (ifdh_cmd, settings['user'], os.path.basename(exe_script))
        f.write(log_cmd)
        if settings['verbose']:
            f.write("########END JOBSETTINGS makeWrapFile #############\n")
        f.close()

    def makeWrapFilePostamble(self):
        """ Make end part of wrapfile ($CONDOR_TMP/user_job_(numbers)_wrap.sh .
        Handle transfer out of user_job generated files via ifdh. Exit with
        exit status of user_job
        """
        settings = self.settings
        ifdh_cmd = settings['ifdh_cmd']
        exe_script = settings['exe_script']
        if settings['transfer_executable']:
            exe_script = os.path.basename(settings['exe_script'])
        script_args = ''
        f = open(settings['wrapfile'], 'a')
        if settings['verbose']:
            f.write("########BEGIN JOBSETTINGS MAKEWRAPFILEPOSTAMBLE#############\n")
        copy_cmd = log_cmd1 = log_cmd2 = cnt = append_cmd = ''
        if len(settings['output_dir_array']) > 0:
            my_tag = "%s:%s" % (settings['user'], os.path.basename(exe_script))
            if settings['use_gftp']:
                copy_cmd = """\t%s cp --force=expgridftp -r -D  """ % ifdh_cmd
            else:
                copy_cmd = """\t%s cp  -D  """ % ifdh_cmd

            for tag in settings['output_dir_array']:
                f.write(
                    "if [ \"$(ls -A ${CONDOR_DIR_%s})\" ]; then\n" % (tag[0]))
                f.write("\tchmod a+rwx ${CONDOR_DIR_%s}/*\n" % tag[0])
                f.write("\t%s mkdir  %s\n" % (ifdh_cmd, tag[1]))
                f.write("fi\n")

                if settings['use_gftp']:
                    copy_cmd = copy_cmd + \
                        """ %s  ${CONDOR_DIR_%s}/ %s """ % (
                            cnt, tag[0], tag[1])
                else:
                    copy_cmd = copy_cmd + \
                        """ %s   ${CONDOR_DIR_%s}/* %s """ % (
                            cnt, tag[0], tag[1])
                    #append_cmd=append_cmd+"""; chmod g+w %s/*"""%tag[1]
                cnt = '\;'

            log_cmd1 = """\t%s log "%s BEGIN %s "\n""" % (
                ifdh_cmd, my_tag, copy_cmd)
            log_cmd2 = """\t%s log "%s FINISHED %s "\n""" % (
                ifdh_cmd, my_tag, copy_cmd)
            f.write("echo `date` BEGIN WRAPFILE COPY-OUT %s\n" % copy_cmd)
            f.write(">&2 echo `date` BEGIN WRAPFILE COPY-OUT %s\n" % copy_cmd)

            f.write(log_cmd1)
            f.write("%s %s\n" % (copy_cmd, append_cmd))
            f.write("echo `date` FINISHED WRAPFILE COPY-OUT %s\n" % copy_cmd)
            f.write(
                ">&2 echo `date` FINISHED WRAPFILE COPY-OUT %s\n" %
                copy_cmd)
            f.write(log_cmd2)

        if settings['joblogfile'] != "" and not settings['nologbuffer']:
            use_gftp = ""
            if settings['use_gftp']:
                use_gftp = "--force=expgridftp"
            if settings['compress_log']:
                f.write("gzip $_CONDOR_SCRATCH_DIR/tmp_job_log_file\n")
                f.write("%s cp %s $_CONDOR_SCRATCH_DIR/tmp_job_log_file.gz %s.gz\n" %
                        (ifdh_cmd, use_gftp, settings['joblogfile']))

            else:
                f.write("%s cp %s $_CONDOR_SCRATCH_DIR/tmp_job_log_file %s\n" %
                        (ifdh_cmd, use_gftp, settings['joblogfile']))

        f.write("exit $JOB_RET_STATUS\n")
        if settings['verbose']:
            f.write("########END JOBSETTINGS MAKEWRAPFILEPOSTAMBLE#############\n")
        f.close
        cmd = "chmod +x %s" % settings['wrapfile']
        commands = JobUtils()
        (retVal, rslt) = commands.getstatusoutput(cmd)

    def wrapFileCopyInput(self):
        """ handle ifdh transfer of input files """

        # print "makeWrapFile"
        settings = self.settings
        f = open(settings['wrapfile'], 'a')
        ifdh_cmd = settings['ifdh_cmd']
        if settings['verbose']:
            f.write("########BEGIN JOBSETTINGS wrapFileCopyInput#############\n")

        f.write("export PATH=\"${PATH}:.\"\n")
        f.write("\n")
        for tag in settings['output_dir_array']:
            f.write("export CONDOR_DIR_%s=${_CONDOR_SCRATCH_DIR}/${PROCESS}/%s\n" %
                    (tag[0], tag[0]))
            f.write("export CONDOR_DEST_DIR_%s=%s\n" %
                    (tag[0], tag[1]))
            f.write("mkdir -p $CONDOR_DIR_%s\n" % tag[0])
            #f.write("mkdir -p $CONDOR_DEST_DIR_%s\n" % tag[0])
            f.write("echo ${CONDOR_DIR_%s}\n" % tag[0])
            f.write("ls -lrt ${CONDOR_DIR_%s}\n" % tag[0])
            f.write("chmod g+rwx $CONDOR_DIR_%s\n\n" % tag[0])

        f.write(
            "export CONDOR_DIR_INPUT=${_CONDOR_SCRATCH_DIR}/${PROCESS}/TRANSFERRED_INPUT_FILES\n")
        f.write("mkdir -p ${_CONDOR_SCRATCH_DIR}/${PROCESS}\n")
        f.write("mkdir -p ${CONDOR_DIR_INPUT}\n")
        if settings['use_gftp']:
            cmd = """%s cp --force=expgridftp  """ % ifdh_cmd
        else:
            cmd = """%s  cp  -D  """ % ifdh_cmd
        cnt = ""
        transfer_file_list = []
        if settings['transfer_input_files'] is not None:
            transfer_file_list = settings['transfer_input_files'].split(',')

        for idir in settings['input_dir_array']:
            if idir in transfer_file_list:
                ifile = os.path.basename(idir)
                f.write("""mv %s ${CONDOR_DIR_INPUT}/\n""" % ifile)
            else:
                cmd = cmd + """ %s %s ${CONDOR_DIR_INPUT}/""" % (cnt, idir)
                cnt = "\;"
        if cnt == "\;":
            f.write("""echo `date` BEGIN WRAPFILE COPY-IN %s\n""" % (cmd))
            f.write(""">&2 echo `date` BEGIN WRAPFILE COPY-IN %s\n""" % (cmd))
            f.write("""%s  log "%s BEGIN %s"\n""" %
                    (ifdh_cmd, settings['user'], cmd))
            f.write("%s\n" % cmd)
            f.write("""%s  log "%s FINISHED %s"\n""" %
                    (ifdh_cmd, settings['user'], cmd))
            f.write("""echo `date` FINISHED WRAPFILE COPY-IN %s\n""" % (cmd))
            f.write(
                """>&2 echo `date` FINISHED WRAPFILE COPY-IN %s\n""" %
                (cmd))

        f.write("\n")

        if settings['transfer_executable'] == False:
            targetdir = '/bin/pwd'
            commands = JobUtils()
            retVal, rslt = commands.getstatusoutput(targetdir)
            f.write("if [ -d %s ]\nthen\n" % rslt)
            f.write("  cd %s\nelse\n" % rslt)
            f.write("  echo Cannot change to submission directory %s\n" % rslt)
            f.write("  echo ...Working dir is thus `/bin/pwd`\n")
            f.write("fi\n")
        if settings['verbose']:
            f.write("########END JOBSETTINGS wrapFileCopyInput#############\n")
        f.close()

    def makeTarDir(self):
        settings = self.settings
        ju = JobUtils()
        if os.path.exists(settings['tar_file_name']) and not settings[
                'overwrite_tar_file']:
            raise IllegalInputError("%s already exists! if you want to overwrite it use --overwrite_tar_file " %
                                    settings['tar_file_name'])
        f = open(settings['tar_file_name'], 'w')
        if not os.path.isdir(settings['input_tar_dir']):
            raise IllegalInputError("%s does not exist or is not a directory " %
                                    settings['input_tar_dir'])
        base = os.path.basename(settings['input_tar_dir'])
        iret, tmpdir = ju.getstatusoutput("/bin/mktemp -d")
        cwd = os.getcwd()
        os.chdir(settings['input_tar_dir'])
        iret, ires = ju.getstatusoutput(
            "tar czvf %s/%s.tgz * " % (tmpdir, base))
        if iret:
            raise Exception(ires)
        f = open('%s/xtract.sh' % tmpdir, 'w')
        f.write(ju.untar_sh())
        f.close()
        iret, ires = ju.getstatusoutput(
            "cat %s/xtract.sh %s/%s.tgz > %s/%s.sh" % (tmpdir, tmpdir, base, tmpdir, base))
        if iret:
            raise Exception(ires)

        iret, ires = ju.getstatusoutput(
            "mv %s/%s.sh %s" % (tmpdir, base, settings['tar_file_name']))
        if iret:
            raise Exception(ires)

        iret, ires = ju.getstatusoutput(
            "chmod +x %s" % (settings['tar_file_name']))
        if iret:
            raise Exception(ires)

    def makeFileTag(self):
        settings = self.settings
        a = settings['exe_script'].split("/")
        prefix = a[-1]
        ow = datetime.datetime.now()
        pid = os.getpid()
        filebase = "%s_%s%02d%02d_%02d%02d%02d_%s" % (prefix, ow.year,
                                                      ow.month, ow.day, ow.hour, ow.minute, ow.second, pid)
        return filebase

    def makeCondorFiles(self):
        # print 'self.makeCondorFiles'
        # sys.exit(0)
        self.checkSanity()
        settings = self.settings
        if settings['input_tar_dir']:
            self.makeTarDir()

        settings['filetag'] = self.makeFileTag()
        if settings['usedagman'] == False:
            self.makeCondorFiles2()
        else:
            if settings['project_name'] == "":
                settings[
                    'project_name'] = "%s-%s" % (settings['user'], settings['filetag'])
            settings['job_count'] = settings['queuecount']
            job_count = settings['queuecount']
            settings['queuecount'] = 1
            job_iter = 1
            while (job_iter <= job_count):
                # print "calling self.makeCondorFiles2(%d)"%job_iter
                self.makeCondorFiles2(job_iter)
                job_iter += 1
                settings['needs_appending'] = False

            self.makeDAGFile()
            env_list = settings['environment']
            settings['environment'] = "%s;JOBSUBJOBSECTION=0" % env_list
            self.replaceLineSetting("""+JobsubJobSection = \"0\"\n""")
            self.makeDAGStart()
            job_iter += 1
            settings['environment'] = "%s;JOBSUBJOBSECTION=%s" % (
                env_list, job_iter)
            self.replaceLineSetting(
                """+JobsubJobSection = \"%s\"\n""" % job_iter )
            self.makeDAGEnd()
            settings['environment'] = env_list

    def makeDAGStart(self):
        if self.settings['dataset_definition'] != "":
            self.makeSAMBeginFiles()
        else:
            self.makeDAGBeginFiles()

    def makeDAGEnd(self):
        if self.settings['dataset_definition'] != "":
            self.makeSAMEndFiles()
        else:
            self.makeDAGEndFiles()

    def makeDAGBeginFiles(self):
        settings = self.settings
        dagbeginexe = "%s.dagbegin.sh" % (settings['filetag'])
        f = open(dagbeginexe, 'wx')
        f.write("#!/bin/sh -x\n")
        f.write("exit 0\n")

        f.close()
        cmd = "chmod +x %s" % dagbeginexe
        commands = JobUtils()
        (retVal, rslt) = commands.getstatusoutput(cmd)

        f = open(settings['dagbeginfile'], 'w')
        f.write("universe          = vanilla\n")
        f.write("executable        = %s\n" % dagbeginexe)
        f.write("arguments         = %s %s %s %s\n" % (settings['group'],
                                                       settings[
                                                           'dataset_definition'],
                                                       settings['project_name'], settings['user']))

        f.write("output                = dagbegin-%s.out\n" %
                (settings['filetag']))
        f.write("error                 = dagbegin-%s.err\n" %
                (settings['filetag']))
        f.write("log                   = dagbegin-%s.log\n" %
                (settings['filetag']))

        f.write("environment = %s\n" % settings['environment'])
        f.write("rank                  = Mips / 2 + Memory\n")
        f.write("notification  = Error\n")
        f.write("+RUN_ON_HEADNODE= True\n")
        f.write("transfer_executable     = True\n")
        f.write("when_to_transfer_output = ON_EXIT_OR_EVICT\n")
        self.handleResourceProvides(f)

        f.write("requirements  = %s\n" % self.condorRequirements())

        f.write("queue 1\n")
        f.close()

    def makeSAMBeginFiles(self):
        settings = self.settings
        sambeginexe = "%s.sambegin.sh" % (settings['filetag'])
        f = open(sambeginexe, 'wx')
        f.write("#!/bin/sh -x\n")
        # f.write("%s\n"%JobUtils().logTruncateString())
        ifdh_pgm_text = JobUtils().ifdhString() % (settings['ifdh_cmd'], settings[
            'wn_ifdh_location'], settings['ifdh_cmd'])
        f.write("%s\n" % ifdh_pgm_text)
        f.write(
            "################################################################################\n")
        f.write(
            "## main ()                                                            ##########\n")
        f.write(
            "################################################################################\n")
        f.write("echo `date` BEGIN executing %s\n" % sambeginexe)
        f.write(">&2 echo `date` BEGIN executing %s\n" % sambeginexe)
        f.write("#EXPERIMENT=$1\n")
        f.write("#DEFN=$2\n")
        f.write("#PRJ_NAME=$3\n")
        f.write("#GRID_USER=$4\n")
        f.write("\n")
        f.write("export JSB_TMP=$_CONDOR_SCRATCH_DIR/jsb_tmp\n")
        f.write("mkdir -p $JSB_TMP\n")
        f.write("setup_ifdh_env\n")
        f.write("%s\n" % JobUtils().krb5ccNameString())
        f.write("\n")
        f.write("""if [ "$SAM_STATION" = "" ]; then\n""")
        f.write("""SAM_STATION=$1\n""")
        f.write("fi\n")
        f.write("""if [ "$SAM_GROUP" = "" ]; then\n""")
        f.write("""SAM_GROUP=$1\n""")
        f.write("fi\n")
        f.write("""if [ "$SAM_DATASET" = "" ]; then\n""")
        f.write("""SAM_DATASET=$2\n""")
        f.write("fi\n")
        f.write("""if [ "$SAM_PROJECT" = "" ]; then\n""")
        f.write("""SAM_PROJECT=$3\n""")
        f.write("fi\n")
        f.write("""if [ "$SAM_USER" = "" ]; then\n""")
        f.write("""SAM_USER=$4\n""")
        f.write("fi\n")
        f.write("""export IFDH_BASE_URI=%s\n""" % settings['ifdh_base_uri'])
        f.write("%s describeDefinition $SAM_DATASET\n" % settings['ifdh_cmd'])
        f.write("%s" % JobUtils().sam_start())
        f.write("exit $SPSTATUS\n")

        f.close()
        cmd = "chmod +x %s" % sambeginexe
        commands = JobUtils()
        (retVal, rslt) = commands.getstatusoutput(cmd)

        f = open(settings['dagbeginfile'], 'w')
        f.write("universe          = vanilla\n")
        f.write("executable        = %s\n" % sambeginexe)
        f.write("arguments         = %s %s %s %s\n" % (settings['group'],
                                                       settings[
                                                           'dataset_definition'],
                                                       settings['project_name'], settings['user']))
        f.write("output                = sambegin-%s.out\n" %
                (settings['filetag']))
        f.write("error                 = sambegin-%s.err\n" %
                (settings['filetag']))
        f.write("log                   = sambegin-%s.log\n" %
                (settings['filetag']))

        f.write("environment = %s\n" % settings['environment'])
        f.write("rank                  = Mips / 2 + Memory\n")
        f.write("notification  = Error\n")
        f.write("+RUN_ON_HEADNODE= True\n")
        f.write("transfer_executable     = True\n")
        f.write("when_to_transfer_output = ON_EXIT_OR_EVICT\n")
        self.handleResourceProvides(f)

        f.write("requirements  = %s\n" % self.condorRequirements())

        f.write("queue 1\n")
        f.close()

    def makeDAGEndFiles(self):
        settings = self.settings
        dagendexe = "%s.dagend.sh" % (
            settings['filetag'])
        f = open(dagendexe, 'wx')
        f.write("#!/bin/sh -x\n")
        f.write("exit 0\n")
        f.close()
        f = open(settings['dagendfile'], 'w')
        f.write("universe          = vanilla\n")
        f.write("executable        = %s\n" % dagendexe)
        f.write("arguments         = %s \n" % (settings['project_name']))
        f.write("output                = dagend-%s.out\n" %
                (settings['filetag']))
        f.write("error                 = dagend-%s.err\n" %
                (settings['filetag']))
        f.write("log                   = dagend-%s.log\n" %
                (settings['filetag']))
        f.write("environment = %s\n" % settings['environment'])
        f.write("rank                  = Mips / 2 + Memory\n")
        f.write("notification  = Error\n")
        f.write("+RUN_ON_HEADNODE= True\n")
        f.write("transfer_executable     = True\n")
        f.write("when_to_transfer_output = ON_EXIT_OR_EVICT\n")
        self.handleResourceProvides(f)
        f.write("requirements  = %s\n" % self.condorRequirements())
        f.write("queue 1\n")

        f.close()
        cmd = "chmod +x %s" % dagendexe
        commands = JobUtils()
        (retVal, rslt) = commands.getstatusoutput(cmd)

    def makeSAMEndFiles(self):
        self.makeDAGEndFiles()
        settings = self.settings
        samendexe = "%s.samend.sh" % (settings['filetag'])
        f = open(samendexe, 'wx')
        f.write("#!/bin/sh -x\n")
        # f.write("%s\n"%JobUtils().logTruncateString())
        ifdh_pgm_text = JobUtils().ifdhString() % (settings['ifdh_cmd'], settings[
            'wn_ifdh_location'], settings['ifdh_cmd'])
        f.write("%s\n" % ifdh_pgm_text)
        f.write("echo `date` BEGIN executing %s\n" % samendexe)
        f.write(">&2 echo `date` BEGIN executing %s\n" % samendexe)
        f.write("export JSB_TMP=$_CONDOR_SCRATCH_DIR/jsb_tmp\n")
        f.write("mkdir -p $JSB_TMP\n")
        f.write("setup_ifdh_env\n")
        f.write("PRJ_NAME=$1\n")
        f.write("\n")
        f.write(JobUtils().krb5ccNameString())
        f.write("\n")
        f.write("""export IFDH_BASE_URI=%s\n""" % settings['ifdh_base_uri'])
        f.write("CPURL=`%s findProject $PRJ_NAME ''` \n" %
                settings['ifdh_cmd'])
        f.write("%s  endProject $CPURL\n" % settings['ifdh_cmd'])
        f.write("EXITSTATUS=$?\n")
        f.write("echo `date` ifdh endProject $CPURL exited with status $EXITSTATUS\n")
        f.write(
            ">&2 echo `date` ifdh endProject $CPURL exited with status $EXITSTATUS\n")
        f.write("exit $EXITSTATUS\n")
        f.close()
        f = open(settings['samendfile'], 'w')
        f.write("universe          = vanilla\n")
        f.write("executable        = %s\n" % samendexe)
        f.write("arguments         = %s \n" % (settings['project_name']))
        f.write("output                = samend-%s.out\n" %
                (settings['filetag']))
        f.write("error                 = samend-%s.err\n" %
                (settings['filetag']))
        f.write("log                   = samend-%s.log\n" %
                (settings['filetag']))
        f.write("environment = %s\n" % settings['environment'])
        f.write("rank                  = Mips / 2 + Memory\n")
        f.write("notification  = Error\n")
        f.write("+RUN_ON_HEADNODE= True\n")
        f.write("transfer_executable     = True\n")
        f.write("when_to_transfer_output = ON_EXIT_OR_EVICT\n")
        self.handleResourceProvides(f)
        f.write("requirements  = %s\n" % self.condorRequirements())
        f.write("queue 1\n")

        f.close()
        cmd = "chmod +x %s" % samendexe
        commands = JobUtils()
        (retVal, rslt) = commands.getstatusoutput(cmd)

    def makeDAGFile(self):
        # print "JobSettings.makeDAGFile()"
        settings = self.settings
        jobname = "DAG"
        if settings['dataset_definition'] != "":
            jobname = "SAM"

        print settings['dagfile']

        f = open(settings['dagfile'], 'w')
        f.write("DOT %s.dot UPDATE\n" % os.path.basename(settings['dagfile']))
        f.write("JOB %s_START %s\n" % (jobname, os.path.basename(settings['dagbeginfile'])))
        if 'firstSection' in settings:
            n = settings['firstSection']
            exe = 'Section'
        else:
            n = 1
            exe = os.path.basename(settings['exe_script'])
        nOrig = n
        for x in settings['cmd_file_list']:
            f.write("JOB %s_%d %s\n" % (exe, n, os.path.basename(x)))
            if settings['mail_summary']:
                f.write("SCRIPT POST %s_%d %s  \n" %
                        (exe, n, settings['dummy_script']))
            n += 1
        f.write("JOB DAG_END %s\n" % (os.path.basename(settings['dagendfile'])))
        samendfile = settings.get('samendfile')
        # if samendfile:
        #f.write("JOB SAM_END %s\n" % samendfile)
        f.write("Parent %s_START child " % jobname)
        n1 = nOrig
        while (n1 < n):
            f.write("%s_%d " % (exe, n1))
            n1 += 1
        f.write("\n")
        f.write("Parent ")
        n1 = nOrig
        while (n1 < n):
            f.write("%s_%d " % (exe, n1))
            n1 += 1
        f.write("child DAG_END\n")
        if samendfile:
            f.write("FINAL SAM_END %s\n" % os.path.basename(samendfile))
        if settings['mail_summary']:
            f.write("SCRIPT POST %s_END %s %s \n" %
                    (jobname, settings['summary_script'], os.path.basename(settings['dagendfile'])))

        f.close()

    def makeCondorFiles2(self, job_iter=0):
        settings = self.settings
        filebase = "%s_%s" % (settings['filetag'], job_iter)
        if settings['dagfile'] == '':
            settings[
                'dagfile'] = "%s/%s.dag" % (settings['condor_tmp'], filebase)
            settings[
                'dagbeginfile'] = "%s/%s.dagbegin.cmd" % (settings['condor_tmp'], filebase)
            settings[
                'dagendfile'] = "%s/%s.dagend.cmd" % (settings['condor_tmp'], filebase)
            if self.settings['dataset_definition'] != "":
                settings[
                    'samendfile'] = "%s/%s.samend.cmd" % (settings['condor_tmp'], filebase)
        uniquer = 0
        retVal = True
        while (retVal):
            uniquer = uniquer + 1
            cmdfile = " %s/%s_%d.cmd" % (
                settings['condor_tmp'], filebase, uniquer)
            retVal = os.path.exists(cmdfile)
            # commands=JobUtils()
            #(retVal,rslt)=commands.getstatusoutput(cmd)
            # if settings['verbose']:
            #    print "%s returns %s - %s " % (cmd, retVal, rslt)

            settings['wrapfile'] = "%s/%s_%s_wrap.sh" % \
                (settings['condor_exec'], filebase, uniquer)
            settings['parrotfile'] = "%s/%s_%s_parrot.sh" % \
                (settings['condor_exec'], filebase, uniquer)
            settings['filebase'] = "%s/%s_%s_" % \
                (settings['condor_tmp'], filebase, uniquer)
            settings['cmdfile'] = settings['filebase'] + ".cmd"

            if settings['verbose']:
                print "settings['wrapfile'] =", settings['wrapfile']
                print "settings['parrotfile'] =", settings['parrotfile']
                print "settings['filebase'] =", settings['filebase']
                print "settings['cmdfile'] =", settings['cmdfile']

            settings['processtag'] = "cluster.$(Cluster).$(Process)"
            # if settings['queuecount']>1:
            #    settings['processtag'] = ".$(Process)"

            settings['logfile'] = settings['filebase'] + ".log"
            settings['errfile'] = settings['filebase'] + \
                settings['processtag'] + ".err"
            settings['outfile'] = settings['filebase'] + \
                settings['processtag'] + ".out"

            if settings['verbose']:
                print "settings['logfile'] =", settings['logfile']
                print "settings['errfile'] =", settings['errfile']
                print "settings['outfile'] =", settings['outfile']
                print "settings['joblogfile'] =", settings['joblogfile']

            for tag in settings['output_tag_array'].keys():
                cmd1 = "%s mkdir  %s " % (settings['ifdh_cmd'], settings[
                                          'output_tag_array'][tag])
                settings['wrapper_cmd_array'].append(cmd1)
                if settings['verbose']:
                    print cmd1
                cmd2 = "chmod g+rw %s " % settings['output_tag_array'][tag]
                settings['wrapper_cmd_array'].append(cmd2)
                if settings['verbose']:
                    print cmd2
                cmd3 = "export CONDOR_DIR_${%s}=\${CONDOR_SCRATCH_DIR/\${PROCESS}/${%s}" % (
                    tag, tag)
                settings['wrapper_cmd_array'].append(cmd3)
                if settings['verbose']:
                    print cmd3
            if settings['usedagman'] == False:
                print"%s" % (settings['cmdfile'])
            if uniquer == 1:
                self.makeCommandFile(job_iter)
                if settings['nowrapfile'] == False:
                    if settings['useparrot'] == False:
                        self.makeWrapFilePreamble()
                        self.makeWrapFile()
                        self.makeWrapFilePostamble()
                    else:
                        self.makeParrotFile()

    def shouldTransferInput(self):
        settings = self.settings
        rsp = "transfer_executable         = False\n"
        if settings['transfer_executable']:
            rsp = "transfer_executable         = True\n"
        tInputFiles = settings['transfer_input_files']
        eScript = settings['exe_script']
        if settings['transfer_executable']:
            if eScript not in tInputFiles and os.path.exists(eScript):
                if len(tInputFiles) > 0:
                    tInputFiles = tInputFiles + ",%s" % eScript
                else:
                    tInputFiles = eScript
        if settings['tar_file_name']:
            t = settings['tar_file_name']
            if t not in tInputFiles and os.path.exists(t):
                if len(tInputFiles) > 0:
                    tInputFiles = tInputFiles + ",%s" % t
                else:
                    tInputFiles = t
        if len(tInputFiles) > 0:
            rsp = rsp + "transfer_input_files = %s\n" % tInputFiles

        return rsp

    def replaceLineSetting(self, thingy):
        settings = self.settings
        if 'lines' in settings:
            parts = thingy.split()
            for line in settings['lines']:
                if parts[0].upper() in line.upper():
                    settings['lines'].remove(line)
            settings['lines'].append(thingy)

    def addToLineSetting(self, thingy):
        settings = self.settings
        if settings['needs_appending']:
            if 'lines' not in settings:
                settings['lines'] = []
            if thingy not in settings['lines']:
                settings['lines'].append(thingy)

    def handleResourceProvides(self, f):
        settings = self.settings
        submit_host = settings['submit_host']
        fp = self.fileParser
        if 'lines' in settings and len(settings['lines']) > 0:
            #print("lines setting=%s"%settings['lines'])
            for thingy in settings['lines']:
                f.write("%s\n" % thingy)
        if 'os' in settings:
            f.write("+DesiredOS =\"%s\"\n" % settings['os'])
        if 'drain' in settings:
            f.write("+Drain = %s\n" % settings['drain'])

        if 'site' in settings and settings['site']:
            if settings['site'] != 'LOCAL':
                f.write("+DESIRED_Sites = \"%s\"\n" % settings['site'])

        if 'blacklist' in settings and settings['blacklist']:
            f.write("+Blacklist_Sites = \"%s\"\n" % settings['blacklist'])

        f.write("+GeneratedBy =\"%s\"\n" % settings['generated_by'])
        for res in settings['resource_list']:
            parts = res.split('=')
            if len(parts) > 1:
                opt = parts[0]
                val = parts[1]
                has_opt = opt
                if 'has_' not in opt.lower():
                    has_opt = "has_%s" % opt
                if not fp.has_option(submit_host, has_opt):
                    optlist = fp.options(submit_host)
                    supported = []
                    for itm in optlist:
                        if 'has_' in itm.lower():
                            supported.append(itm[4:])

                    err = " --resource-provides=%s is not configured on %s . Try --resource-provides=(one of %s) " % (
                        opt, submit_host, supported)
                    raise InitializationError(err)
                else:
                    allowed_vals = fp.get(submit_host, has_opt)
                    allowed_vals = allowed_vals.replace(', ', ',')
                    allowed_vals = allowed_vals.replace(' ,', ',')
                    allowed_vals = allowed_vals.upper()
                    allowed_list = allowed_vals.split(',')
                    vals_ok = False
                    val_list = val.split(',')
                    for check_val in val_list:
                        if check_val.strip().upper() in allowed_list:
                            vals_ok = True
                    if not vals_ok:
                        err = " --resource-provides=%s=%s is not configured on %s .  Legal values are --resource-provides=%s=(one of %s)" %\
                            (opt, val, submit_host, opt, allowed_vals.upper())
                        raise InitializationError(err)
                    else:
                        f.write("""+DESIRED_%s = "%s"\n""" % (opt, val))

    def condorRequirements(self):
        # print "condorRequirements
        # needs_appending=%s"%self.settings['needs_appending']
        settings = self.settings
        if settings['needs_appending']:
            self.makeCondorRequirements()
        return settings['requirements']

    def completeEnvList(self):
        envDict = {
            'GRID_USER': 'user',
            'EXPERIMENT': 'group',
            'IFDH_BASE_URI': 'ifdh_base_uri',
            'INPUT_TAR_FILE': 'tar_file_basename',
            'JOBSUBJOBID': 'jobsubjobid',
            'JOBSUBPARENTJOBID': 'jobsubparentjobid',
        }
        samDict = {
            'SAM_USER': 'user',
            'SAM_GROUP': 'group',
            'SAM_STATION': 'group',
            'SAM_DATASET': 'dataset_definition',
            'SAM_PROJECT': 'project_name',
            'SAM_PROJECT_NAME': 'project_name',
        }
        self.addEnv(envDict)
        if self.settings['dataset_definition'] != "":
            self.addEnv(samDict)

    def addEnv(self, adict):
        envStr = self.settings['environment']
        l1 = len(envStr)
        for key in adict.keys():
            k2 = key + "="
            if envStr.find(k2) < 0:
                val = adict[key]
                if val in self.settings and self.settings[val] != '':
                    envStr = "%s;%s=%s" % (envStr, key, self.settings[val])
        l2 = len(envStr)
        if l2 > l1:
            self.settings['environment'] = envStr

    def makeCondorRequirements(self):
        settings = self.settings
        if 'needs_appending' in settings and settings['needs_appending']==False:
            return settings['requirements']
        settings['needs_appending'] = False

        if 'overwriterequirements' in settings:
            settings['requirements'] = settings['overwriterequirements']
            return settings['requirements']

        bval = self.fileParser.get('default','requirements_base')
        if bval:
            settings['requirements'] = bval

        if 'grid' in settings and settings['grid']:
            _default = '&& (target.IS_Glidein==true) '
            gval = self.fileParser.get('default','requirements_is_glidein')
            if not gval:
                gval = _default
            settings['requirements'] = settings['requirements'] + gval


        if 'site' in settings and settings['site']:
            _default = '&& (stringListIMember(target.GLIDEIN_Site,my.DESIRED_Sites)) '
            sval = self.fileParser.get('default', 'requirements_site')
            if not sval:
                sval = _default
            settings['requirements'] = settings['requirements'] +  sval

        if 'blacklist' in settings and settings['blacklist']:
            _default = '&& (stringListIMember(target.GLIDEIN_Site,my.Blacklist_Sites)) '
            sval = self.fileParser.get('default', 'requirements_blacklist')
            if not sval:
                sval = _default
            settings['requirements'] = settings['requirements'] +  sval

        if 'desired_os' in settings and settings['desired_os']:
            settings['requirements'] = settings[
                'requirements'] + settings['desired_os']

        if 'resource_list' in settings:
            for x in settings['resource_list']:
                (opt, val) = x.split('=')
                settings['requirements'] = settings['requirements'] +\
                    """ && (stringListsIntersect(toUpper(target.HAS_%s),""" % (opt) +\
                    """ toUpper(my.DESIRED_%s)))""" % (opt)

        if 'append_requirements' in settings:
            for req in settings['append_requirements']:
                settings['requirements'] = settings[
                    'requirements'] + " && %s " % req

        return settings['requirements']

    def makeCommandFile(self, job_iter=0):
        settings = self.settings
        settings['cmd_file_list'].append(settings['cmdfile'])
        f = open(settings['cmdfile'], 'w')
        f.write("universe          = vanilla\n")

        f.write("executable        = %s\n" % os.path.basename(settings['wrapfile']))
        args = ""
        for arg in settings['script_args']:
            args = args + " " + arg + " "
        if job_iter <= 1:
            for arg in settings['added_environment']:
                settings['environment'] = settings['environment'] + ";" +\
                    arg + '=' + os.environ.get(arg, 'NOT_SET')
            self.completeEnvList()
        env_list = settings['environment']
        if settings['usedagman'] and 'JOBSUBJOBSECTION' \
                not in settings['added_environment']:
            env_list = "%s;JOBSUBJOBSECTION=%s" % (
                settings['environment'], job_iter)
            self.replaceLineSetting(
                """+JobsubJobSection = \"%s\"\n""" % job_iter)
        f.write("arguments         = %s\n" % args)
        f.write("output                = %s\n" % os.path.basename(settings['outfile']))
        f.write("error                 = %s\n" % os.path.basename(settings['errfile']))
        f.write("log                   = %s\n" % os.path.basename(settings['logfile']))
        f.write("environment   = %s\n" % env_list)
        f.write("rank                  = Mips / 2 + Memory\n")
        f.write("job_lease_duration = %s\n" %
                settings.get('job_lease_duration', '7200'))

        if settings['notify'] == 0:
            f.write("notification  = Never\n")
        elif settings['notify'] == 1:
            f.write("notification  = Error\n")
        else:
            f.write("notification  = Always\n")
        f.write("when_to_transfer_output = ON_EXIT_OR_EVICT\n")
        f.write("transfer_output                 = True\n")
        f.write("transfer_output_files = .empty_file\n")
        f.write("transfer_error                  = True\n")
        tval = self.shouldTransferInput()
        f.write(tval)

        if 'notify_user' not in settings:
            settings['notify_user'] = "%s@%s" % (settings['user'],
                                                 settings['mail_domain'])

        self.addToLineSetting("notify_user = %s" % settings['notify_user'])
        if settings['grid']:
            self.addToLineSetting("x509userproxy = %s" %
                                  settings['x509_user_proxy'])
            self.addToLineSetting("+RunOnGrid                          = True")

            if not settings['site']:
                if settings['default_grid_site']:
                    settings['site'] = settings['default_grid_site']

        if settings['istestjob'] == True:
            self.addToLineSetting("+AccountingGroup = \"group_testjobs\"")

        if settings['group'] != "" and settings['istestjob'] == False:
            if settings['subgroup']:
                self.addToLineSetting("+AccountingGroup = \"group_%s.%s.%s\"" %
                                      (settings['accountinggroup'], settings['subgroup'],
                                       settings['user']))
            else:
                self.addToLineSetting("+AccountingGroup = \"group_%s.%s\"" %
                                      (settings['accountinggroup'], settings['user']))
        self.addToLineSetting("+Jobsub_Group=\"%s\"" % settings['group'])
        self.addToLineSetting("+JobsubJobId=\"%s\"" % settings['jobsubjobid'])
        if settings['subgroup']:
            self.addToLineSetting("+Jobsub_SubGroup=\"%s\"" %
                                  settings['subgroup'])

        self.handleResourceProvides(f)

        if 'disk' in settings:
            f.write("request_disk = %s\n" % settings['disk'])
        if 'memory' in settings:
            f.write("request_memory = %s\n" % settings['memory'])
        if 'cpu' in settings:
            f.write("request_cpus = %s\n" % settings['cpu'])

        f.write("requirements  = %s\n" % self.condorRequirements())

        f.write("\n")
        f.write("\n")
        f.write("queue %s" % settings['queuecount'])

        f.close()
