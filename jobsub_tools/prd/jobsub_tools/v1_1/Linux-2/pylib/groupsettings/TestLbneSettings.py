#!/usr/bin/env python
# $Id$

import unittest
from TestJobSettings import JobTest
from JobSettings import JobSettings
from LbneSettings import LbneSettings


class LbneTest(JobTest):

    def setUp(self):
        self.ns = LbneSettings()


    def testLbneConstructor(self):

        ns = self.ns    
        self.assertEqual(ns.settings['lbne_condor'],
                         ns.settings['group_condor'])
        self.assertEqual(ns.settings['defaultrelarea'],
                         '/grid/fermiapp/lbne/software_releases')
        super(LbneTest,self).testConstructor()


    def testLbneGoodInput(self):
        #print "TestLbneSettings testGoodInput"
        ns = self.ns
        ns.runParser(['-ilalalala','test_script'])
        self.assertEqual(ns.settings['reldir'],'lalalala')
        ns.runParser(['-tlalalala','test_script'])
        self.assertEqual(ns.settings['testreldir'],'lalalala')
        ns.runParser(['-rlalalala','test_script'])
        self.assertEqual(ns.settings['rel'],'lalalala')
        super(LbneTest,self).testGoodInput()

        
    def testLbneBadInput(self):

        ns = self.ns
        self.assertRaises(SystemExit,ns.runParser,
                          ['--deliberately_bogus_option','lalalala'],2)
        super(LbneTest,self).testBadInput()
                         


if __name__ == "__main__":
    #unittest.main()
    suite = unittest.makeSuite(LbneTest)
    unittest.TextTestRunner(verbosity=10).run(suite)
