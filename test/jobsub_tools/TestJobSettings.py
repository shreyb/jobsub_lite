#!/usr/bin/env python
# $Id$

import unittest
import sys
import os
import commands
import tempfile
#from test import test_support

from JobSettings import JobSettings




class JobTest(unittest.TestCase):

#    def __init__(self):
#        self.stdout = sys.stdout
#        self.stderr = sys.stderr
#        self.devnull = open(os.devnull,'w')
#        
#        return super(unittest.TestCase,self).__init__()
#        

    currentResult = None # holds last result object passed to run method

    def run(self, result=None):
        self.currentResult = result # remember result for use in tearDown
        unittest.TestCase.run(self, result) # call superclass run method

    def ioSetUp(self):
        self.stdout=sys.stdout
        self.stderr=sys.stderr
        self.devnull=open(os.devnull,'w')
        self.stdioOFF()

    def stdioON(self):
        sys.stderr=self.stderr
        sys.stdout=self.stderr

    def stdioOFF(self):
        sys.stderr=self.devnull
        sys.stdout=self.devnull

    def setUp(self):
        """set up JobSettings"""
        self.tmpdir=tempfile.mkdtemp()

        os.environ['CONDOR_TMP']=self.tmpdir
        os.environ['CONDOR_EXEC']=self.tmpdir
        if not hasattr(self,'ns'):
            self.ioSetUp()
            self.stdioOFF()
            setattr(self,'ns',JobSettings())
        self.ns.settings['condor_tmp']=self.tmpdir
        self.ns.settings['condor_exec']=self.tmpdir
        self.stdioON()

    def tearDown(self):
        #ok = self.currentResult.wasSuccessful()
        errors = self.currentResult.errors
        failures = self.currentResult.failures
        ok = len(self.currentResult.errors) == 0 and len(self.currentResult.failures) == 0
        self.stdioON()
        if len(errors) > 0  or len (failures) > 0:
                print """test failed, output saved to %s"""%self.tmpdir
                print """ errors: %s """ % errors
                print """ failures: %s """ % failures
        else:
                #print "test ok, removing %s"%self.tmpdir
                import shutil
                shutil.rmtree(self.tmpdir)

    def testConstructor(self):
        """test that JobSettings constructor initializes correctly"""
        #self.setUp()
        ns = self.ns
    
        self.assertEqual(ns.settings['output_tag_array'],{})

        self.assertEqual(ns.settings['condor_tmp'],self.tmpdir)
        self.assertEqual(ns.settings['condor_exec'],self.tmpdir)
        self.assertEqual(ns.settings['condor_config'],None)
        self.assertNotEqual(ns.settings['local_condor'],None)
        self.assertNotEqual(ns.settings['group_condor'],None)
        self.assertNotEqual(ns.settings['x509_user_proxy'],None)
        
        self.assertEqual(ns.settings['input_dir_array'],[])
        self.assertEqual(ns.settings['istestjob'],False)
        self.assertEqual(ns.settings['needafs'],False)
        self.assertEqual(ns.settings['notify'],1)
        self.assertEqual(ns.settings['submit'],True)
        self.assertEqual(ns.settings['grid'],False)
        self.assertEqual(ns.settings['usepwd'],True)
        self.assertEqual(ns.settings['forceparrot'],False)
        self.assertEqual(ns.settings['forcenoparrot'],True)
        self.assertNotEqual(ns.settings['environment'],None)
        self.assertEqual(ns.settings['lines'],[])
        self.assertNotEqual(ns.settings['group'],None)
        self.assertNotEqual(ns.settings['user'],None)
        self.assertEqual(ns.settings['output_tag_counter'],0)
        self.assertEqual(ns.settings['input_tag_counter'],0)
        self.assertEqual(ns.settings['queuecount'],1)
        self.assertEqual(ns.settings['joblogfile'],"")
        self.assertEqual(ns.settings['override_x509'],False)
        self.assertEqual(ns.settings['use_gftp'],0)
        self.assertEqual(ns.settings['filebase'],'')
        self.assertEqual(ns.settings['wrapfile'],'')
        self.assertEqual(ns.settings['parrotfile'],'')
        self.assertEqual(ns.settings['cmdfile'],'')
        self.assertEqual(ns.settings['processtag'],'')
        self.assertEqual(ns.settings['logfile'],'')
        self.assertEqual(ns.settings['opportunistic'],0)
        self.assertEqual(ns.settings['errfile'],'')
        self.assertEqual(ns.settings['outfile'],'')
        self.assertEqual(ns.settings['msopt'],"")
        self.assertEqual(ns.settings['exe_script'],'')
        self.assertEqual(ns.settings['script_args'],[])
        self.assertEqual(ns.settings['verbose'], False)
        self.assertEqual(ns.settings['wrapper_cmd_array'],[])
        self.assertEqual(ns.settings['msopt'],"")
        self.assertNotEqual(ns.settings['generated_by'],"")
        self.stdioOFF()
        self.assertEqual(ns.checkSanity(),True)
        self.stdioON()
    
        
    def testGoodInput(self):

        
        """test  JobSettings correct  input flags"""
        #self.setUp()

        ns = self.ns
        #ns = JobSettings()
        
        #ns.runCmdParser(["-ooutput_dir1","--output=output_dir2","my_script"],None)
        #self.assertEqual(ns.settings['output'],['output_dir1','output_dir2'])
        #ns.runCmdParser(["-a","my_script"], None)
        self.assertEqual(ns.settings['needafs'],False)
        self.assertEqual(ns.settings['drain'],False)
        ns.runCmdParser(['--drain','dummy_script'])
        self.assertEqual(ns.settings['drain'],True)
        self.assertEqual(ns.settings['forceparrot'],False)
        ns.runCmdParser(['-Glalalala','some_script'])
        self.assertEqual(ns.settings['accountinggroup'],'lalalala')
        ns.runCmdParser(['--group=thats_a_silly_group_name','some_script'])
        self.assertEqual(ns.settings['accountinggroup'],'thats_a_silly_group_name')
        ns.runCmdParser(['-N 10','shhhhh.sh'])
        self.assertEqual(ns.settings['queuecount'],10)
        ns.runCmdParser(['-q','shhhhh.sh'])
        self.assertEqual(ns.settings['notify'],1)
        ns.runCmdParser(['-Q','SSSSHHHHH.sh'])
        self.assertEqual(ns.settings['notify'],0)
        logfile = ns.settings['condor_tmp']+'/testlogfile'
        ns.runCmdParser(["-L%s"%logfile, 'some_script'])
        self.assertEqual(ns.settings['joblogfile'],logfile)
        ns.runCmdParser(['-g','some_script'])
        self.assertEqual(ns.settings['grid'],True)
        #del ns
        
    def testBadInput(self):
        """give JobSettings some bad input -- should complain"""
        #self.setUp()
        ns = self.ns
        #ns = JobSettings()
        self.stdioOFF()
        self.assertRaises(SystemExit,ns.runCmdParser,
                          ['--deliberately_bogus_option','lalalala'],2)
    
        self.stdioON()
        
    def testMakingDagFiles(self):
        """test whether DAG files for SAM made correctly"""
        #self.assertTrue(True)
        """test that JobSettings creates cmdfile, wrapfile """
        ns = self.ns
        #ns = JobSettings()
        
        #print "%s"%ns.settings
        self.stdioOFF()
        ns.settings['dataset_definition']="mwm_test_1"
        ns.settings['queuecount']=3
        ns.settings['accountinggroup']="group_w"
        ns.settings['exe_script']=ns.__class__.__name__+"_samtest.sh"
        ns.settings['grid']=True
        ns.makeCondorFiles()
        self.stdioON()

        self.assertEqual(os.path.isfile(ns.settings['dagfile']),True,ns.settings['dagfile'])
        self.assertEqual(os.path.isfile(ns.settings['dagbeginfile']),True,ns.settings['dagbeginfile'])
        self.assertEqual(os.path.isfile(ns.settings['dagendfile']),True,ns.settings['dagendfile'])
        
        (retVal,output)=commands.getstatusoutput("grep RunOnGrid  %s"%ns.settings['cmdfile'])
        self.assertEqual(retVal,0,"file %s did not contain 'RunOnGrid' "%ns.settings['cmdfile'])


        #(retVal,output)=commands.getstatusoutput("grep RUN_ON_HEADNODE %s"%ns.settings['dagbeginfile'])
        #self.assertEqual(retVal,0)
        
        #(retVal,output)=commands.getstatusoutput("grep RUN_ON_HEADNODE %s"%ns.settings['dagendfile'])
        #self.assertEqual(retVal,0)

        cmd="wc -l %s"%ns.settings['dagfile']
        (retVal,output)=commands.getstatusoutput(cmd)
        response="9 %s"%ns.settings['dagfile']
        self.assertEqual(retVal,0,"command '%s' should have exited with status 0, got %s instead"%(cmd,retVal))
        self.assertEqual(output,response,"expected '%s' from '%s', got '%s' instead"%(output,cmd,response))
        #del ns
        
    def testMakingCommandFiles(self):
        """test that JobSettings creates cmdfile, wrapfile """
        ns = self.ns
        #ns = JobSettings()
        
        #print "%s"%ns.settings
        self.stdioOFF()
        ns.settings['queuecount']=11
        ns.settings['accountinggroup']="group_w"
        ns.settings['exe_script']=ns.__class__.__name__+"_MakeCommandFiles.sh"
        ns.settings['set_expected_max_lifetime']='10m'
        ns.makeCondorFiles()
        #ns.makeParrotFile()
        self.stdioON()
        self.assertEqual(os.path.isfile(ns.settings['cmdfile']),True,ns.settings['cmdfile'])
        self.assertEqual(os.path.isfile(ns.settings['wrapfile']),True,ns.settings['wrapfile'])
        #self.assertEqual(os.path.isfile(ns.settings['parrotfile']),True,ns.settings['parrotfile'])
        cmd="grep group_group_w %s"%ns.settings['cmdfile']
        (retVal,output)=commands.getstatusoutput(cmd)
        self.assertEqual(retVal,0,"%s exited with status %s"%(cmd,retVal))
        
        self.assertEqual(output.find('+AccountingGroup = "group_group_w'),0)
        (retVal,output)=commands.getstatusoutput("grep 'queue 1' %s"%ns.settings['cmdfile'])
        self.assertEqual(retVal,0)
        
        (retVal,output)=commands.getstatusoutput("grep RunOnGrid  %s"%ns.settings['cmdfile'])
        self.assertNotEqual(retVal,0)
        #del ns

    def testTimeoutFlag(self):
        """test --timeout option"""
        ns = self.ns
        ns.runCmdParser(['--timeout=5m','some_script'])
        self.assertEqual(ns.settings['timeout'],'5m')
        ns.checkSanity()
        self.stdioOFF()
        ns.makeCondorFiles()
        self.stdioON()
        (retVal,output)=commands.getstatusoutput("grep '^timeout 5m $JOBSUB_EXE_SCRIPT'  %s"%ns.settings['wrapfile'])
        self.assertEqual(retVal,0,ns.settings['wrapfile'])

    def testEnvFlag(self):
        """test -e FOO=BAR option"""
        ns = self.ns
        ns.runCmdParser(['-e','FOO=BAR','some_script'])
        ns.checkSanity()
        self.assertEqual(ns.settings['added_environment'],['FOO'])
        self.assertEqual(os.environ.get('FOO'),'BAR')
        self.stdioOFF()
        ns.checkSanity()
        ns.makeCondorFiles()
        self.stdioON()
        cmd = "grep 'environment ' %s"%ns.settings['cmdfile']
        (retVal,output)=commands.getstatusoutput(cmd)
        self.assertEqual(retVal,0,'envrionment = not in '+ns.settings['cmdfile'])
        self.assertTrue('FOO=BAR' in output)


    def testExpectedLifetimeFlag(self):
        """test --expected-lifetime option"""
        ns = self.ns
        ns.runCmdParser(['--expected-lifetime=10m','some_script'])
        ns.checkSanity()
        self.assertEqual(ns.settings['set_expected_max_lifetime'],'10m')
        self.stdioOFF()
        ns.checkSanity()
        ns.makeCondorFiles()
        self.stdioON()
        cmd = "grep '^\s*+JOB_EXPECTED_MAX_LIFETIME\s*=\s*600\s*$' %s"%ns.settings['cmdfile']
        (retVal,output)=commands.getstatusoutput(cmd)
        self.assertEqual(retVal, 0, 'JOB_EXPECTED_MAX_LIFETIME not in ' + ns.settings['cmdfile'])

    def testDiskFlag(self):
        """test --disk option"""
        ns = self.ns
        ns.runCmdParser(['--disk=10GB','some_script'])
        ns.checkSanity()
        self.assertEqual(ns.settings['disk'],'10GB')
        self.stdioOFF()
        ns.checkSanity()
        ns.makeCondorFiles()
        self.stdioON()
        cmd = "grep '^\s*request_disk\s*=\s*10GB\s*$'  %s"%ns.settings['cmdfile']
        (retVal,output)=commands.getstatusoutput(cmd)
        self.assertEqual(retVal, 0, cmd)

    def testMemoryFlag(self):
        """test --memory option"""
        ns = self.ns
        ns.runCmdParser(['--memory=10GB','some_script'])
        ns.checkSanity()
        self.assertEqual(ns.settings['memory'],'10GB')
        self.stdioOFF()
        ns.checkSanity()
        ns.makeCondorFiles()
        self.stdioON()
        cmd = "grep '^\s*request_memory\s*=\s*10GB\s*$'  %s"%ns.settings['cmdfile']
        (retVal,output)=commands.getstatusoutput(cmd)
        self.assertEqual(retVal, 0, cmd)

    def testCPUFlag(self):
        """test --cpu option"""
        ns = self.ns
        ns.runCmdParser(['--cpu=4','some_script'])
        ns.checkSanity()
        self.assertEqual(ns.settings['cpu'],4)
        self.stdioOFF()
        ns.checkSanity()
        ns.makeCondorFiles()
        self.stdioON()
        cmd = "grep '^\s*request_cpus\s*=\s*4\s*$'  %s"%ns.settings['cmdfile']
        (retVal,output)=commands.getstatusoutput(cmd)
        self.assertEqual(retVal, 0, cmd)

    def testOSFlag(self):
        """test --OS option"""
        ns = self.ns
        ns.runCmdParser(['--OS=SL6,SL7','some_script'])
        ns.checkSanity()
        self.assertEqual(ns.settings['os'],"SL6,SL7")
        self.stdioOFF()
        ns.checkSanity()
        ns.makeCondorFiles()
        self.stdioON()
        cmd = "grep -i '+desiredos'  %s"%ns.settings['cmdfile']
        (retVal,output)=commands.getstatusoutput(cmd)
        self.assertEqual(retVal, 0, cmd)
        self.assertTrue('"SL6,SL7"' in output)
        cmd = "grep -i 'requirements'  %s"%ns.settings['cmdfile']
        (retVal,output)=commands.getstatusoutput(cmd)
        self.assertTrue('stringlistimember(Target.IFOS_installed,DesiredOS)'.upper() in output.upper())

    def testResourceProvidesFlag(self):
        """test --resource-provides option"""
        ns = self.ns
        ns.runCmdParser(['--resource-provides=usage_model=DEDICATED,OPPORTUNISTIC','some_script'])
        ns.checkSanity()
        self.assertEqual(ns.settings['resource_list'],['usage_model=DEDICATED,OPPORTUNISTIC'])
        self.stdioOFF()
        ns.checkSanity()
        ns.makeCondorFiles()
        self.stdioON()
        cmd = "grep -i '+desired_usage_model'  %s"%ns.settings['cmdfile']
        (retVal,output)=commands.getstatusoutput(cmd)
        self.assertEqual(retVal, 0, cmd)
        self.assertTrue('"DEDICATED,OPPORTUNISTIC"' in output)
        cmd = "grep -i 'requirements'  %s"%ns.settings['cmdfile']
        (retVal,output)=commands.getstatusoutput(cmd)
        self.assertTrue('stringListsIntersect(toUpper(target.HAS_usage_model), toUpper(my.DESIRED_usage_model)'.upper() in output.upper())

    def testSiteFlag(self):
        """test --site option"""
        ns = self.ns
        ns.runCmdParser(['--site=SITE_A,SITE_B','some_script'])
        ns.checkSanity()
        self.assertEqual(ns.settings['site'],'SITE_A,SITE_B')
        self.stdioOFF()
        ns.checkSanity()
        ns.makeCondorFiles()
        self.stdioON()
        cmd = "grep -i '+DESIRED_Sites'  %s"%ns.settings['cmdfile']
        (retVal,output)=commands.getstatusoutput(cmd)
        self.assertEqual(retVal, 0, cmd)
        self.assertTrue('"SITE_A,SITE_B"' in output)
        cmd = "grep -i 'requirements'  %s"%ns.settings['cmdfile']
        (retVal,output)=commands.getstatusoutput(cmd)
        self.assertTrue('stringListIMember(target.GLIDEIN_Site,my.DESIRED_Sites)'.upper() in output.upper())

    def testBlacklistFlag(self):
        """test --blacklist option"""
        ns = self.ns
        ns.runCmdParser(['--blacklist=SITE_A,SITE_B','some_script'])
        ns.checkSanity()
        self.assertEqual(ns.settings['blacklist'],'SITE_A,SITE_B')
        self.stdioOFF()
        ns.checkSanity()
        ns.makeCondorFiles()
        self.stdioON()
        cmd = "grep -i '+Blacklist_Sites'  %s"%ns.settings['cmdfile']
        (retVal,output)=commands.getstatusoutput(cmd)
        self.assertEqual(retVal, 0, cmd)
        self.assertTrue('"SITE_A,SITE_B"' in output)
        cmd = "grep -i 'requirements'  %s"%ns.settings['cmdfile']
        (retVal,output)=commands.getstatusoutput(cmd)
        self.assertTrue('stringListIMember(target.GLIDEIN_Site,my.Blacklist_Sites)=?=false'.upper() in output.upper())

    def testCPNCommands(self):
        """test CPN i/o from -d and -f flags"""
        ##jobsub -f input_file_1 -f input_file_2 -d FOO this_is_the_foo_dir -d BAR this_is_the_bar_dir (some_subclass)_CPNtest.sh
        ns = self.ns
        ns.settings['input_dir_array']=['input_file_1', 'input_file_2']
        ns.settings['output_dir_array']=[('FOO', 'this_is_the_foo_dir'),('BAR', 'this_is_the_bar_dir')]
        ns.settings['accountinggroup']="group_w"
        ns.settings['exe_script']=ns.__class__.__name__+"_CPNtest.sh"
        self.stdioOFF()
        ns.makeCondorFiles()
        self.stdioON()
        (retVal,output)=commands.getstatusoutput("grep -P 'ifdh.sh\s+cp\s+-D\s+input_file_1\s+\$\{CONDOR_DIR_INPUT\}\/ \\\; input_file_2 \$\{CONDOR_DIR_INPUT\}\/'  %s"%ns.settings['wrapfile'])
        self.assertEqual(retVal,0,'cpn cant find input_file_1 in '+ns.settings['wrapfile'])

        (retVal,output)=commands.getstatusoutput("grep -P 'ifdh.sh\s+cp\s+-D\s+\$\{CONDOR_DIR_FOO\}\/\*\s+this_is_the_foo_dir\s+\\\;\s+\$\{CONDOR_DIR_BAR\}\/\*\s+this_is_the_bar_dir' %s"%ns.settings['wrapfile'])
        self.assertEqual(retVal,0,'cpn cant transfer out CONDOR_DIR_FOO in file '+ns.settings['wrapfile'])
        
        
    def testGFTPCommands(self):
        """test gridFTP i/o from -d and -f flags"""
        ##jobsub --use_gftp  -f input_file_1 -f input_file_2 -d FOO this_is_the_foo_dir -d BAR this_is_the_bar_dir (some_subclass)_GFTPtest.sh
        ns = self.ns
        ns.settings['input_dir_array']=['input_file_1', 'input_file_2']
        ns.settings['output_dir_array']=[('FOO', 'this_is_the_foo_dir'),('BAR', 'this_is_the_bar_dir')]
        ns.settings['accountinggroup']="group_w"
        ns.settings['exe_script']=ns.__class__.__name__+"_GFTPtest.sh"
        ns.settings['use_gftp']=True
        self.stdioOFF()
        ns.makeCondorFiles()
        self.stdioON()
        (retVal,output)=commands.getstatusoutput("grep -P 'ifdh.sh\s+cp\s+--force=expgridftp\s+input_file_1\s+\$\{CONDOR_DIR_INPUT\}\/\s+\\\;\s+input_file_2\s+\$\{CONDOR_DIR_INPUT\}\/' %s"%\
                                                 (ns.settings['wrapfile']))

        self.assertEqual(retVal,0,'gftp cant find input_file_1 in '+ns.settings['wrapfile'])

        
        (retVal,output)=commands.getstatusoutput("grep -P 'ifdh.sh\s+cp\s+--force\=expgridftp -r -D\s+\$\{CONDOR_DIR_FOO\}\/\s+this_is_the_foo_dir\s+\\\;\s+\$\{CONDOR_DIR_BAR\}\/\s+this_is_the_bar_dir' %s"%\
                                                 (ns.settings['wrapfile']))
        self.assertEqual(retVal,0,'gftp cant transfer out CONDOR_DIR_BAR in file '+ns.settings['wrapfile'])
        
       
        

if __name__ == "__main__":
    
    #unittest.main()
    suite = unittest.makeSuite(JobTest)
    unittest.TextTestRunner(verbosity=10).run(suite)

