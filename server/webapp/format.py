import cherrypy
import logger
import json

from pprint import pformat


def htmlPrintItemList(src, dpth=0, key=''):
    s = ''
    tabs = lambda n: ' ' * n * 4
    if isinstance(src, dict):
        if key:
            s = '%s%s<li>%s:</li>\n' % (s, tabs(dpth), key)
        s = '%s%s<ul>\n' % (s, tabs(dpth))
        for key, value in src.iteritems():
            s = '%s%s' % (s, htmlPrintItemList(value, dpth + 1, key))
        s = '%s%s</ul>\n' % (s, tabs(dpth))
    elif isinstance(src, list):
        s = '%s%s<ul>\n' % (s, tabs(dpth))
        for litem in src:
            s = '%s%s' % (s, htmlPrintItemList(litem, dpth + 2, key))
        s = '%s%s</ul>\n' % (s, tabs(dpth))
    else:
        if key:
            s = '%s%s<li>%s: %s</li>' %(s, tabs(dpth), key, src)
        else:
            s = '%s%s<li>%s</li>' %(s, tabs(dpth), src)
    return s


def _format_response(content_type, data, log_response=True):
    logger.log('Response Content-Type: %s' % content_type)
    if log_response:
        logger.log('Response: %s' % (data))
    content_type_list = content_type.split(',')
    if 'application/json' in content_type_list:
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return str(json.dumps(data))
    elif 'text/plain' in content_type_list:
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return str(pformat(data))
    elif 'text/html' in content_type_list:
        cherrypy.response.headers['Content-Type'] = 'text/html'
        return '<html><body>%s</body></html>' % htmlPrintItemList(data)
    elif 'application/x-download' in content_type_list:
        return data
    else:
        return 'Content type %s not supported' % content_type


def format_response(func):
    def format_response_wrapper(*args, **kwargs):
        cherrypy.response.headers['Content-Type'] = None
        data = func(*args, **kwargs)
        content_type_accept = cherrypy.request.headers.get('Accept')
        content_type_response = cherrypy.response.headers['Content-Type']
        content_type = (content_type_response or content_type_accept)
        log_response = True
        if args[0].__module__ in ('jobsub_help', 'dag_help'):
            log_response = False

        return _format_response(content_type, data, log_response=log_response)

    return format_response_wrapper
