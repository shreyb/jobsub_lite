import logging
import cherrypy


def log(msg='', context='', severity=logging.INFO, traceback=False):
    try:
        logger.log(msg, context, severity, traceback)
    except:
        logging.log(severity, msg)
