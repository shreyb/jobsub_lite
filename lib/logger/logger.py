import logging
import cherrypy


def log(msg='', context='', severity=logging.INFO, traceback=False):
    try:
        cherrypy.request.app.log.error(msg, context, severity, traceback)
    except:
        logging.log(severity, msg)
