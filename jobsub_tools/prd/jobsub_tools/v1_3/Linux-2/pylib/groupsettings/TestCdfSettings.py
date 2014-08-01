#!/usr/bin/env python
# $Id$

import unittest,sys
from TestJobSettings import JobTest
#from JobSettings import JobSettings
from CdfSettings import CdfSettings


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


    def testCdfGoodInput(self):
	""" Test Cdf Good Input"""
        ns=self.ns
        ns.runCmdParser(['--outLocation=outLocationValue','some_script'])
        self.assertEqual(ns.settings['outLocation'],'outLocationValue','setting --outLocation Test FAILED')
        ns.runCmdParser(['--procType=procTypeValue','procTypeValue'])
        self.assertEqual(ns.settings['procType'],'procTypeValue','setting --procType test FAILED')
        ns.runCmdParser(['--start=startValue','startValue'])
        self.assertEqual(ns.settings['start'],'startValue','setting --start FAILED')
        super(CdfTest,self).testGoodInput()

        
    def testCdfBadInput(self):

	""" Test Cdf Bad Input"""
        ns = self.ns
        super(CdfTest,self).testBadInput()
                         


if __name__ == "__main__":
    #unittest.main()
    suite = unittest.makeSuite(CdfTest)
    unittest.TextTestRunner(verbosity=10).run(suite)
