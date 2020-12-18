# file: compat_check.py
# project: jobsub
# author: Dennis Box, dbox@fnal.gov
# purpose: detect if the python environment has been altered
# since ups 'setup jobsub_client' command has been altered
# in a way that will make jobsub commands fail
#

import sys
import os

# get python version jobsub was set up for
env_pyver  = os.environ.get('JOBSUB_PYVER')

# get current python version
runtime_pyver = "python%s.%s" % (sys.version_info[0],sys.version_info[1])
if runtime_pyver == "python2.7":
    uc_size = str(sys.maxunicode)
    if uc_size == "1114111":
        runtime_pyver += "-ucs4"
    else:
        runtime_pyver += "-ucs2"

# helpful error message if needed
err = "Problem with python compatibility libraries detected. "
err +="Jobsub is setup for %s, but %s is ahead of it in the PATH. " % (env_pyver, runtime_pyver)
err +="The easiest way to fix this is with the unix ups command 'setup jobsub_client'. "
err +="This will pre-load the correct compatibility libraries for %s" % runtime_pyver

if runtime_pyver != env_pyver:
    raise Exception(err)

#everything seems to be OK, load compatibility layer
from future import standard_library
try:
    standard_library.install_aliases()
except Exception as err1:
    err += "sucks to be you"
    print(err)
    raise Exception(err1)

