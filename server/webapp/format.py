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


def _format_response(content_type, data):
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
    else:
        return 'Content type %s not supported' % content_type


def format_response(func):
    def wrapper(*args, **kwargs):
        content_type_accept = cherrypy.request.headers.get('Accept')
        logger.log('Request content_type_accept: %s' % content_type_accept)
        return _format_response(content_type_accept, func(*args, **kwargs))

    return wrapper