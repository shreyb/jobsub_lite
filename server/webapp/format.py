"""
 Description:
   This module implements various html formatting functions

 Project:
   JobSub

 Author:
   Nick Palumbo

"""
import cherrypy
import json
from functools import partial
from pprint import pformat


def htmlPrintItemList(src, dpth=0, key=''):
    s = ''

    def tabs(n): return ' ' * n * 4
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
        s = '%s%s<li>%s</li>\n' % (s, tabs(dpth), src)
    return s


def htmlPrintPreformatted(src):
    return """<pre>%s</pre>""" % _htmlPrintPreformatted(src)


def _htmlPrintPreformatted(src, dpth=0, key=''):
    s = ''
    if isinstance(src, dict):
        if key:
            s = '%s%s' % (s, key)
        for key, value in src.iteritems():
            s = '%s%s' % (s, _htmlPrintPreformatted(value, key))
    elif isinstance(src, list):
        s = '%s%s' % (s, '\n'.join(src))
    else:
        s = '%s%s' % (s, src)
    return s


def htmlPrintTableList(src):
    return """<table>%s</table>""" % _htmlPrintTableList(src)


def _htmlPrintTableList(src, dpth=0, key=''):
    s = ''
    if isinstance(src, dict):
        if key:
            s = '%s<tr><td>%s:</td></tr>\n' % (s, key)
        for key, value in src.iteritems():
            s = '%s%s' % (s, _htmlPrintTableList(value, key))
    elif isinstance(src, list):
        for litem in src:
            s = '%s%s' % (s, _htmlPrintTableList(litem, key))
    else:
        s = '%s<tr><td>%s</td></tr>\n' % (s, src)
    return s


def rel_link(itm, exp=None):
    content_type_accept = cherrypy.request.headers.get('Accept')
    content_type_list = content_type_accept.split(',')
    if 'application/json' in content_type_list:
        return itm
    if 'text/html' not in content_type_list:
        return itm
    if not exp:
        exp = itm
    return "<a href=%s/>%s</a>" % (itm, exp)


def styleSheets():
    # put style sheet info in here once we decide what we want
    style = """
    """
    return style


def _format_response(content_type, data, output_format=None):
    """do the actual work of formatting output based on
       content_type.
       accepted values of content_type are:
           'application/json', 'text/plain', or 'text/html'
    """
    content_type_list = content_type.split(',')
    if 'application/json' in content_type_list:
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return str(json.dumps(data))
    elif 'text/plain' in content_type_list:
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return str(pformat(data))
    elif 'text/html' in content_type_list:
        cherrypy.response.headers['Content-Type'] = 'text/html'
        if hasattr(cherrypy.request, 'output_format'):
            output_format = getattr(cherrypy.request, 'output_format', None)
        if output_format == 'pre':
            return '<html><head>%s</head><body>%s</body></html>' % (
                styleSheets(), htmlPrintPreformatted(data))
        elif output_format == 'table':
            return '<html><head>%s</head><body>%s</body></html>' % (
                styleSheets(), htmlPrintTableList(data))
        else:
            return '<html><head>%s</head><body>%s</body></html>' % (
                styleSheets(), htmlPrintItemList(data))
    elif 'application/x-download' in content_type_list:
        return data
    else:
        return 'Content type %s not supported' % content_type


def format_response(func=None, output_format=None):
    """entry point for @format_response decorator
       args: output_format:
                if output_format=="pre"
                    return output wrapped with <pre></pre>
                else
                    return 'normal' html output

    """
    if func is None:
        return partial(format_response, output_format=output_format)

    #@wraps(func)
    def wrapper(*args, **kwargs):
        cherrypy.response.headers['Content-Type'] = None
        data = func(*args, **kwargs)
        content_type_accept = cherrypy.request.headers.get('Accept')
        content_type_response = cherrypy.response.headers['Content-Type']
        content_type = (content_type_response or content_type_accept)

        return _format_response(
            content_type, data, output_format=output_format)

    return wrapper
