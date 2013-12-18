#!/usr/bin/env python
# $Id$

import unittest
from JobSettings import JobSettings
from MinervaSettings import MinervaSettings
from TestJobSettings import JobTest

 
class MinervaTest(JobTest):


    def setUp(self):
        self.ns = MinervaSettings()


    def testMinervaConstructor(self):
        """exercise MinervaSettings constructor"""
        ns = self.ns
    
        #self.assertEqual(ns.settings['minerva_condor'],
        #                 ns.settings['group_condor'])
        self.assertEqual(ns.settings['defaultrelarea'],
                         '/grid/fermiapp/minerva/software_releases')
        self.assertEqual(ns.settings['msopt'],'')
        self.assertEqual(ns.settings['enstorefiles'],'')


    def testMinervaGoodInput(self):
        """exercise Minervsettings against good input """
        ns = self.ns
        #ns.parseArgs('-i','lalalala')
        ns.runParser(['-ilalalala','a_script'])
        self.assertEqual(ns.settings['reldir'],'lalalala')
        #ns.parseArgs('-t','lalalala')
        ns.runParser(['-tlalalala','a_script'])
        self.assertEqual(ns.settings['testreldir'],'lalalala')
        #ns.parseArgs('-r','lalalala')
        ns.runParser(['-rlalalala','a_script'])
        self.assertEqual(ns.settings['rel'],'lalalala')
        
        ns.runParser(['-yenstore1','a_script'])
        self.assertEqual(ns.settings['enstorefiles'],['enstore1'])
        ns.runParser(['-yenstore1', '-yenstore2','a_script'])
        self.assertEqual(ns.settings['enstorefiles'],['enstore1', 'enstore2'])
        
        ns.runParser(['-O','a_script'])
        self.assertEqual(ns.settings['msopt'],'-O')
        
        #ns.runParser(["-ooutput_dir1","--output=output_dir2","my_script"],None)
        #self.assertEqual(ns.settings['output'],['output_dir1','output_dir2'])

        
    def testMinervaBadInput(self):

        """excercise MinervaSettings against bad input -- should complain"""
        ns = self.ns
        self.assertRaises(SystemExit,ns.runParser,
                          ['--deliberately_bogus_option','lalalala'],2)
                         


if __name__ == "__main__":
    #unittest.main()
    suite = unittest.makeSuite(MinervaTest)
    unittest.TextTestRunner(verbosity=10).run(suite)
