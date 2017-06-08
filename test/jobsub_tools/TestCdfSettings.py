#!/usr/bin/env python
# $Id$

import unittest,sys
from TestJobSettings import JobTest
#from JobSettings import JobSettings
from CdfSettings import CdfSettings
from JobSettings import InitializationError


class CdfTest(JobTest):

    def setUp(self):
        super(CdfTest,self).ioSetUp()
        self.ns = CdfSettings()
        super(CdfTest,self).setUp()

    def testCdfConstructor(self):

        """ Test Cdf Constructor"""
        ns = self.ns    
        #self.assertEqual('up','down','I create my own reality')
        super(CdfTest,self).testConstructor()

    def testTimeoutFlag(self):
        self.assertEqual(True,False,'forgot to implement --timeout flag for this class')


    def testCdfGoodInput(self):
        """ Test Cdf Good Input"""
        ns=self.ns
        ns.runCmdParser(['--outLocation=outLocationValue','some_script'])
        self.assertEqual(ns.settings['outLocation'],'outLocationValue','setting --outLocation Test FAILED')
        ns.runCmdParser(['--sections=1-3','some_script'])
        self.assertEqual(ns.settings['sectionList'],'1-3',' --sections test FAILED')
        ns.checkSanity()
        self.assertEqual(ns.settings['firstSection'],1,'start FAILED after checkSanity')
        self.assertEqual(ns.settings['lastSection'],3,'end FAILED after checkSanity')

        super(CdfTest,self).testGoodInput()

        
                         

        
    def testCdfBadInput(self):
        """give CdfSettings some bad input -- should complain"""
        ns = self.ns
        ns.runCmdParser(['--start=-3','some_script'])
        self.assertRaises(SystemExit,ns.checkSanity)
        ns.runCmdParser(['--start=3','some_script'])
        ns.runCmdParser(['--end=1','some_script'])
        self.assertRaises(SystemExit,ns.checkSanity)
    
        

if __name__ == "__main__":
    #unittest.main()
    suite = unittest.makeSuite(CdfTest)
    unittest.TextTestRunner(verbosity=10).run(suite)
