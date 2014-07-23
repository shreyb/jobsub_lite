#!/usr/bin/env python
# $Id$

import unittest
from TestJobSettings import JobTest
#from JobSettings import JobSettings
from CdfSettings import CdfSettings


class CdfTest(JobTest):

    def setUp(self):
        self.ns = CdfSettings()
        super(CdfTest,self).setUp()

    def testCdfConstructor(self):

        ns = self.ns    
        #self.assertEqual('up','down','I create my own reality')
        super(CdfTest,self).testConstructor()


    def testCdfGoodInput(self):
        super(CdfTest,self).testGoodInput()

        
    def testCdfBadInput(self):

        ns = self.ns
        super(CdfTest,self).testBadInput()
                         


if __name__ == "__main__":
    #unittest.main()
    suite = unittest.makeSuite(CdfTest)
    unittest.TextTestRunner(verbosity=10).run(suite)
