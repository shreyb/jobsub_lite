#!/usr/bin/env python
import unittest2 as unittest
import jobsub

"""Unit test for jobsub/server/webapp/jobsub.py functions
   TODO: These tests are very dependent on the contents of jobsub.ini
   and should not use the default one stored on the server, it can change
"""

class jobsub_function_tests(unittest.TestCase):


    def test_is_supported_accountinggroup(self):
        grp = 'nova'
        v = jobsub.is_supported_accountinggroup(grp)
        self.assertEqual(v,True)

        grp = 'patagonian_seperatists'
        v = jobsub.is_supported_accountinggroup(grp)
        self.assertEqual(v,False)

    def test_group_superusers(self):
        grp = 'nova'
        v = jobsub.group_superusers(grp)
        self.assertIsInstance(v,list)

    def test_is_superuser_for_group(self):
        grp = 'minerva'
        user='rodriges'
        self.assertTrue(jobsub.is_superuser_for_group(grp,user))
        grp = 'nova'
        self.assertFalse(jobsub.is_superuser_for_group(grp,user))

    def test_sandbox_readable_by_group(self):
        grp = 'nova'
        self.assertTrue(jobsub.sandbox_readable_by_group(grp))
        grp = 'patriot'
        self.assertFalse(jobsub.sandbox_readable_by_group(grp))

    def test_sandbox_allowed_browsable_file_type(self):
        tl = jobsub.sandbox_allowed_browsable_file_types()
        self.assertIsInstance(tl, list)
        self.assertTrue( '.log' in tl )

    def test_get_supported_accountinggroups(self):
        tl = jobsub.get_supported_accountinggroups()
        self.assertIsInstance(tl, list)
        self.assertTrue( 'nova' in tl )

    def test_default_voms_role(self):
        tl = jobsub.default_voms_role()
        self.assertIsInstance(tl, str)
        self.assertEqual('Analysis', tl)

    def test_sub_group_pattern(self):
        grp = 'marsaccel'
        tl = jobsub.sub_group_pattern(grp)
        self.assertIsInstance(tl, str)
        self.assertEqual('mars/accel', tl)

    def test_get_authentication_methods(self):
        grp = 'nova'
        tl = jobsub.get_authentication_methods(grp)
        self.assertIsInstance(tl, list)
        self.assertTrue( 'myproxy' in tl )

    def test_get_submit_reject_threshold(self):
        tl = jobsub.get_submit_reject_threshold()
        self.assertIsInstance(tl, float)

    def test_get_command_path_root(self):
        tl = jobsub.get_command_path_root()
        self.assertIsInstance(tl, str)
        self.assertEqual('/fife/local/scratch/uploads',tl)

    def test_should_transfer_krb5cc(self):
        grp = 'cdf'
        self.assertTrue(jobsub.should_transfer_krb5cc(grp))
        grp = 'patriot'
        self.assertFalse(jobsub.should_transfer_krb5cc(grp))

    def test_get_dropbox_path_root(self):
        tl = jobsub.get_dropbox_path_root()
        self.assertIsInstance(tl, str)
        self.assertEqual('/fife/local/scratch/dropbox',tl)

    def test_get_jobsub_wrapper(self):
        tl = jobsub.get_jobsub_wrapper()
        self.assertIsInstance(tl, str)
        self.assertEqual('/opt/jobsub/server/webapp/jobsub_env_runner.sh',tl)
        tl = jobsub.get_jobsub_wrapper('dag')
        self.assertEqual('/opt/jobsub/server/webapp/jobsub_dag_runner.sh',tl)

if __name__ == '__main__':
        #unittest.main(buffer=True)
        suite = unittest.TestLoader().loadTestsFromTestCase(jobsub_function_tests)
        unittest.TextTestRunner(verbosity=2).run(suite)
