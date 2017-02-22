#!/usr/bin/env python
import unittest2 as unittest
import condor_commands

"""Unit test for jobsub/server/webapp/condor_commands.py functions
"""

class condor_commands_tests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_ui_condor_userprio(self):
        up = condor_commands.ui_condor_userprio()
        self.assertIsInstance(up,str)
        self.assertNotEqual('',up)
        self.assertNotIn("""Traceback""", up)

    def test_ui_condor_status_totalrunningjobs(self):
        up = condor_commands.ui_condor_status_totalrunningjobs()
        self.assertIsInstance(up,str)
        self.assertNotEqual('',up)
        self.assertNotIn("""Traceback""", up)

    def test_ui_condor_queued_jobs_summary(self):
        up = condor_commands.ui_condor_queued_jobs_summary()
        self.assertIsInstance(up,str)
        self.assertNotEqual('',up)
        self.assertNotIn("""Traceback""", up)

    def test_condor_header(self):
        up = condor_commands.condor_header()
        self.assertIsInstance(up,str)
        self.assertNotEqual('',up)
        self.assertNotIn("""Traceback""", up)

    def test_condor_format(self):
        up = condor_commands.condor_format()
        self.assertIsInstance(up,str)
        self.assertNotEqual('',up)
        self.assertNotIn("""Traceback""", up)

    def test_constructFilter(self):
        up = condor_commands.constructFilter()
        self.assertIsInstance(up,str)
        self.assertIn("""-constraint 'True && True && True && True'""",up)

        up = condor_commands.constructFilter(acctgroup='nova')
        self.assertIsInstance(up,str)
        self.assertIn("""-constraint \'regexp("group_nova.*",AccountingGroup) && True && True && True\'""",up)

        up = condor_commands.constructFilter(uid='dbox')
        self.assertIsInstance(up,str)
        self.assertIn("""-constraint \'True && Owner=="dbox" && True && True\'""",up)

        up = condor_commands.constructFilter(jobid='333.0@fifebatch1.fnal.gov')
        self.assertIsInstance(up,str)
        self.assertIn("""-constraint \'True && True && regexp("fifebatch1.fnal.gov#333.0.*",GlobalJobId) && True\'""", up)

        for k in condor_commands.JOBSTATUS_DICT.keys():
            up = condor_commands.constructFilter(jobstatus=k)
            self.assertIsInstance(up,str)
            self.assertIn("""-constraint 'True && True && True && JobStatus==%s'""" % condor_commands.JOBSTATUS_DICT[k], up)

        up = condor_commands.constructFilter(acctgroup="nova",jobstatus="held",uid="dbox") 
        self.assertIsInstance(up,str)
        self.assertIn("""-constraint \'regexp("group_nova.*",AccountingGroup) && Owner=="dbox" && True && JobStatus==5\'""", up)

    @unittest.skip("come back to this one...")
    def test_ui_condor_q(self):
        filt = condor_commands.constructFilter(acctgroup="nova",jobstatus="held",uid="dbox")
        up = condor_commands.ui_condor_q(filt,'long')
        self.assertIsInstance(up,str)
        self.assertNotIn("""Traceback""", up)

    def test_condor_userprio(self):
        up = condor_commands.condor_userprio()
        self.assertIsInstance(up,str)
        self.assertNotIn("""Traceback""", up)

    def test_iwd_condor_q(self):

        filt = condor_commands.constructFilter(acctgroup="nova",jobstatus="held",uid="dbox")
        up = condor_commands.iwd_condor_q(filt)
        self.assertIsInstance(up,str)
        self.assertNotIn("""Traceback""", up)

        up = condor_commands.iwd_condor_q(filt,a_part='NumShadowStarts')
        self.assertIsInstance(up,str)
        self.assertNotIn("""Traceback""", up)


    def test_collector_host(self):
        up = condor_commands.collector_host()
        self.assertIsInstance(up,str)
        self.assertNotIn("""Traceback""", up)
        self.assertNotEqual('',up)

    def test_schedd_list(self):
        up = condor_commands.schedd_list()
        self.assertIsInstance(up,list)
        self.assertNotEqual([''],up)
    
    def test_schedd_recent_duty_cycle(self):
        up = condor_commands.schedd_recent_duty_cycle()
        self.assertIsInstance(up,float)

    def test_schedd_name(self):
        up = condor_commands.schedd_name()
        self.assertIsInstance(up,str)
        self.assertNotIn("""Traceback""", up)
        self.assertNotEqual('',up)



if __name__ == '__main__':
        #unittest.main(buffer=True)
        suite = unittest.TestLoader().loadTestsFromTestCase(condor_commands_tests)
        unittest.TextTestRunner(verbosity=2).run(suite)
