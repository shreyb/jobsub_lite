#!/usr/bin/env python
import unittest2 as unittest
import JobsubConfigParser
import os
import socket

"""Unit test for jobsub/lib/JobsubConfigParser/JobsubConfigParser.py functions
   TODO: These tests are very dependent on the contents of jobsub.ini
   and should not use the default one stored on the server, it can change
"""

class jobsub_config_parser_tests(unittest.TestCase):

    def setUp(self):
        self.parser = JobsubConfigParser.JobsubConfigParser()

    def test_get_submit_host(self):
        smh = self.parser.get_submit_host()
        self.assertIsInstance(smh, str)
        self.assertTrue(len(smh)>0)

    def test_sections(self):
        scl = self.parser.sections()
        self.assertIsInstance(scl, list)
        self.assertTrue(len(scl)>0)

    def test_iniFile(self):
        scl = self.parser.iniFile()
        self.assertIsInstance(scl, str)
        self.assertTrue(len(scl)>0)
        self.assertTrue(os.path.exists(scl))

    def test_options(self):
        itms = self.parser.options('nova')
        self.maxDiff = None
        itms2= self.parser.items('nova')
        valdict = dict(itms2)
        self.assertEqual(itms.sort(), valdict.keys().sort())


    def test_has_section(self):
        self.assertEqual(True,self.parser.has_section('nova'))
        self.assertEqual(False,self.parser.has_section('nihlists_with_an_ethos'))

    @unittest.skip("come back to this one...") 
    def test_has_option(self):
        itm = self.parser.has_option('nova','hash_nondefault_proxy')
        self.assertEqual(True, itm)
        itm = self.parser.has_option('nova','nihlists_with_an_ethos')
        self.assertEqual(False, itm)
        #this is contrary to the documentation and fails, which is why it is 
        #skipped. Changing it might break things
        itm = self.parser.has_option('nova','supported_roles')
        self.assertEqual(True, itm)

    def test_items(self):
        itms = self.parser.items('nova')
        self.assertIsInstance(itms, list)
        self.assertTrue(len(itms)>0)

    def test_get(self):
        itm = self.parser.get('nova','hash_nondefault_proxy')
        self.assertEqual(True,itm)
        itm = self.parser.get('minos','sandbox_readable_by_group')
        self.assertFalse(itm)
        itm = self.parser.get('nihlists_with_an_ethos','sandbox_readable_by_group')
        self.assertFalse(itm)

    def test_supportedRoles(self):
        srl = self.parser.supportedRoles()
        self.assertIsInstance(srl, list)
        self.assertTrue(len(srl)>0)

    def test_supportedGroups(self):
        sgl = self.parser.supportedGroups()
        self.assertIsInstance(sgl, list)
        self.assertTrue(len(sgl)>0)

    def test_findConfigFile(self):
        cfg = self.parser.findConfigFile()
        self.assertTrue(os.path.exists(cfg))




if __name__ == '__main__':
        #unittest.main(buffer=True)
        suite = unittest.TestLoader().loadTestsFromTestCase(jobsub_config_parser_tests)
        unittest.TextTestRunner(verbosity=2).run(suite)
