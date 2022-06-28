import os
import sys
import time

import pytest
from jinja2 import exceptions

#
# we assume everwhere our current directory is in the package 
# test area, so go ahead and cd there
#
os.chdir(os.path.dirname(__file__))


#
# import modules we need to test, since we chdir()ed, can use relative path
#
sys.path.append("../lib")
import creds
import utils

from test_unit import TestUnit 

if not os.path.exists("jobsub_submit.py"):
    os.symlink("../bin/jobsub_submit", "jobsub_submit.py")
import jobsub_submit


class TestJobsubSubmitUnit:
    """
        Use with pytest... unit tests for ../lib/*.py
    """

    # jobsub_submit functions

    def test_get_basefiles_1(self):
        """ test the get_basefiles routine on our source directory,
            we should be in it """
        dlist = [ os.path.dirname(__file__) ]
        fl = jobsub_submit.get_basefiles(dlist)
        assert os.path.basename(__file__) in fl

    def test_render_files_1(self):
        """ test render files on the dataset_dag directory """
        srcdir = os.path.dirname(os.path.dirname(__file__)) + "/templates/dataset_dag"
        dest = "/tmp/out{0}".format(os.getpid())
        os.mkdir(dest)
        args = {**TestUnit.test_vargs, **TestUnit.test_extra_template_args}
        jobsub_submit.render_files(srcdir, args, dest)
        assert os.path.exists("%s/dagbegin.cmd" % dest)

    def test_render_files_undefined_vars(self, tmp_path):
        """Test rendering files when a template variable is undefined.  
        Should raise jinja2.exceptions.UndefinedError
        """
        test_vargs = {}
        srcdir = os.path.dirname(os.path.dirname(__file__)) + "/templates/simple"
        dest = tmp_path
        args = {**TestUnit.test_vargs, **TestUnit.test_extra_template_args}
        with pytest.raises(exceptions.UndefinedError, match="is undefined"):
            jobsub_submit.render_files(srcdir, args, dest)
        

    def test_cleanup_1(self):
        # cleanup doesn't actually do anything right now...
        jobsub_submit.cleanup("")
        assert True

    def test_do_dataset_defaults_1(self):
        """ make sure do_dataset_defaults sets arguments its supposed to
        """
        varg = TestUnit.test_vargs.copy()
        varg['dataset_definition'] = 'mwmtest'
        utils.set_extras_n_fix_units(varg, TestUnit.test_schedd, "", "")
        jobsub_submit.do_dataset_defaults(varg)
        for var in ["PROJECT", "DATASET", "USER", "GROUP", "STATION"]:
            assert repr(varg["environment"]).find("SAM_%s"%var) > 0

