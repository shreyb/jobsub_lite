import logging
import cherrypy
import os
import sys
from threading import current_thread

# File: FakeLogger.py
# Purpose: redirects jobsub logging to stdout
# Author Dennis Box, dbox@fnal.gov
#
# Usage:  import FakeLogger as logger  in jobsub code
#        useful for unit testing
#        if $JOBSUB_SUPPRESS_LOG_OUTPUT is defined, no logging occurs
#        else logging goes to stdout


def whereAmI(nFramesUp=1):
    """ Create a string naming the function n frames up on the stack.
    """
    co = sys._getframe(nFramesUp + 1).f_code
    return "[%s:%s:%s]" % (current_thread().ident,
                           os.path.basename(co.co_filename), co.co_name)


def init_logger(logger_name, log_file, level=logging.INFO):
    pass


def get_logger(logger_name, level=logging.INFO):
    pass


def log(msg='', context='', severity=logging.INFO,
        traceback=False, logfile=None):
    if os.getenv('JOBSUB_SUPPRESS_LOG_OUTPUT'):
        return

    here = whereAmI()
    msg = '%s %s' % (here, msg)
    if logfile:
        print("LOG [file=%s] [severity=%s] %s %s" %
              (logfile, severity, msg, traceback))
    elif cherrypy.request.app is None:
        logfile = log_file_name(here)
        print("LOG [file=%s] [severity=%s] %s %s" %
              (logfile, severity, msg, traceback))
    else:
        print(
            "LOG [file=debug] [severity=%s] %s %s" %
            (severity, msg, traceback))


def log_file_name(whereFrom):
    logFileName = "krbrefresh"
    if whereFrom is not None:
        if whereFrom.find('jobsub_preen') >= 0:
            logFileName = "jobsub_preen"
    return logFileName
