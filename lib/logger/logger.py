import logging
import cherrypy
import os

def log(msg='', context='', severity=logging.INFO, traceback=False):
    if cherrypy.request.app is None:
        setup_admin_logger()
        log_to_admin(msg,context,severity,traceback)
    else:
        try:
            cherrypy.request.app.log.error(msg, context, severity, traceback)
        except:
            logging.log(severity, msg)

def setup_admin_logger():
    log_dir = os.environ.get("JOBSUB_LOG_DIR")
    log_file = "%s/admin.log"%log_dir
    logging.basicConfig(format='%(asctime)s %(message)s ', filename=log_file,level=logging.DEBUG)


def log_to_admin(msg='', context='', severity=logging.INFO, traceback=False):
    logging.debug(msg)
