import logging
import cherrypy
import os
import sys
from threading import current_thread


def whereAmI(nFramesUp=1):
    """ Create a string naming the function n frames up on the stack.
    """
    co = sys._getframe(nFramesUp + 1).f_code
    return "[%s:%s:%s]" % (current_thread().ident,
                           os.path.basename(co.co_filename), co.co_name)
    # return "[%s:%d %s]" % (os.path.basename(co.co_filename),
    # co.co_firstlineno,co.co_name)


def init_logger(logger_name, log_file, level=logging.INFO):
    l = logging.getLogger(logger_name)
    try:
        foo = l.hasBeenSet
    except Exception:
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s]  %(message)s')
        fileHandler = logging.FileHandler(log_file, mode='a')
        fileHandler.setFormatter(formatter)
        l.setLevel(level)
        l.addHandler(fileHandler)
        l.hasBeenSet = True
    return l


def get_logger(logger_name, level=logging.INFO):
    log_dir = os.environ.get('JOBSUB_LOG_DIR', '/var/log/jobsub')
    log_file = "%s/%s.log" % (log_dir, logger_name)
    l = init_logger(logger_name, log_file, level=level)
    l.propagate = False
    return l


def log(msg='', context='', severity=logging.INFO,
        traceback=False, logfile=None):
    here = whereAmI()
    msg = '%s %s' % (here, msg)
    if logfile:
        l = get_logger(logfile)
        l.log(severity, msg, exc_info=traceback)
    elif cherrypy.request.app is None:
        logfile = log_file_name(here)
        l = get_logger(logfile)
        l.log(severity, msg, exc_info=traceback)
    else:
        try:
            cherrypy.request.app.log.error(msg, context, severity, traceback)
        except Exception:
            logging.log(severity, msg)


def log_file_name(whereFrom):
    logFileName = "krbrefresh"
    if whereFrom is not None:
        if whereFrom.find('jobsub_preen') >= 0:
            logFileName = "jobsub_preen"
    return logFileName
