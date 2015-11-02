#!/usr/bin/env python
# $Id$

import unittest
from TestJobSettings import JobTest
#from JobSettings import JobSettings
from LbneSettings import LbneSettings


class LbneTest(JobTest):

    def setUp(self):
        super(LbneTest,self).ioSetUp()
        self.ns = LbneSettings()
        super(LbneTest,self).stdioON()
        super(LbneTest,self).setUp()

    def testLbneConstructor(self):

        ns = self.ns    
        self.assertEqual(ns.settings['condor_tmp'], self.tmpdir)
        self.assertEqual(ns.settings['lbne_condor'],
                         ns.settings['group_condor'])
        self.assertEqual(ns.settings['defaultrelarea'],
                         '/grid/fermiapp/lbne/software_releases')
        super(LbneTest,self).testConstructor()


    def testLbneGoodInput(self):
        #print "TestLbneSettings testGoodInput"
        ns = self.ns
        ns.runCmdParser(['-ilalalala','test_script'])
        self.assertEqual(ns.settings['reldir'],'lalalala')
        ns.runCmdParser(['-tlalalala','test_script'])
        self.assertEqual(ns.settings['testreldir'],'lalalala')
        ns.runCmdParser(['-rlalalala','test_script'])
        self.assertEqual(ns.settings['rel'],'lalalala')
        super(LbneTest,self).testGoodInput()

        
    def testLbneBadInput(self):

        ns = self.ns
        self.stdioOFF()
        self.assertRaises(SystemExit,ns.runCmdParser,
                          ['--deliberately_bogus_option=dumb_stuff','lalalala'],2)
        self.stdioON()
        super(LbneTest,self).testBadInput()
                         


if __name__ == "__main__":
    #unittest.main()
    suite = unittest.makeSuite(LbneTest)
    unittest.TextTestRunner(verbosity=10).run(suite)
