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
            setattr(self,'ns',JobSettings())
        self.ns.settings['condor_tmp']=self.tmpdir
        self.ns.settings['condor_exec']=self.tmpdir
        self.stdioON()

    def tearDown(self):
        ok = self.currentResult.wasSuccessful()
        errors = self.currentResult.errors
        failures = self.currentResult.failures
        self.stdioON()
        if ok:
                #print "test ok, removing %s"%self.tmpdir
                import shutil
                shutil.rmtree(self.tmpdir)
        else:
                print """test failed, output saved to %s"""%self.tmpdir

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
        self.assertEqual(ns.checkSanity(),True)
    
        
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
        ns.runCmdParser(['-T','huh'])
        self.assertEqual(ns.settings['istestjob'],True)
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
        response="8 %s"%ns.settings['dagfile']
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

