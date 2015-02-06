import logging
import cherrypy
import os
import sys

def whereAmI(nFramesUp=1):
    """ Create a string naming the function n frames up on the stack.
    """
    co = sys._getframe(nFramesUp+1).f_code
    return "[%s:%s]" % (os.path.basename(co.co_filename), co.co_name)
    #return "[%s:%d %s]" % (os.path.basename(co.co_filename), co.co_firstlineno,co.co_name)

def log(msg='', context='', severity=logging.INFO, traceback=False):
    here = whereAmI()
    msg = '%s %s' % (here, msg)
    if cherrypy.request.app is None:
        setup_admin_logger(here)
        log_to_admin(msg,context,severity,traceback)
    else:
        try:
            cherrypy.request.app.log.error(msg, context, severity, traceback)
        except:
            logging.log(severity, msg)

def log_file_name(whereFrom):
    logFileName="krbrefresh.log"
    if whereFrom is not None:
	if whereFrom.find('jobsub_preen')>=0:
		logFileName="jobsub_preen.log"
    return logFileName

def setup_admin_logger(wherefrom=None):
    log_dir = os.environ.get('JOBSUB_LOG_DIR', '/var/log/jobsub')
    #log_dir = '/var/log/jobsub'
    log_file = "%s/%s"%(log_dir,log_file_name(wherefrom))
    logging.basicConfig(format='%(asctime)s %(message)s ', filename=log_file,level=logging.DEBUG)


def log_to_admin(msg='', context='', severity=logging.INFO, traceback=False):
    logging.debug(msg)
