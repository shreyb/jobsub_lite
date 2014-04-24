#!/usr/bin/env python
# $Id$

import unittest
from TestJobSettings import JobTest
#from JobSettings import JobSettings
from NovaSettings import NovaSettings


class NovaTest(JobTest):

    def setUp(self):
        self.ns = NovaSettings()

    def testNovaConstructor(self):
        """exercise NovaSettings constructor"""
        ns = self.ns
    
        self.assertEqual(ns.settings['nova_condor'],
                         ns.settings['group_condor'])
        self.assertEqual(ns.settings['defaultrelarea'],
                         '/grid/fermiapp/nova/software_releases')
        super(NovaTest,self).testConstructor()

    def testNovaGoodInput(self):
        #print "TestNovaSettings testGoodInput"
        ns = self.ns
        #print "%s"%ns
        #ns.parseArgs('-v', 1)
        ns.runCmdParser(['-ilalalala','some_script'])
        self.assertEqual(ns.settings['reldir'],'lalalala')
        ns.runCmdParser(['-tlalalala','some_script'])
        self.assertEqual(ns.settings['testreldir'],'lalalala')
        ns.runCmdParser(['-rlalalala','some_script'])
        self.assertEqual(ns.settings['rel'],'lalalala')
        super(NovaTest,self).testGoodInput()

        
    def testNovaBadInput(self):

        ns = self.ns
        self.assertRaises(SystemExit,ns.runCmdParser,
                          ['--deliberately_bogus_option','lalalala'])
        super(NovaTest,self).testBadInput()
                         


if __name__ == "__main__":
    #unittest.main()
    suite = unittest.makeSuite(NovaTest)
    unittest.TextTestRunner(verbosity=10).run(suite)
