import cherrypy
import json

from pprint import pformat


def htmlPrintItem(obj, indent):
    s = ''
    if isinstance(obj, dict):
        for k, v in obj.iteritems():
            s = '%s %s %s %s %s %s' % (s, '  ' * indent, '<li>', str(k), ':', '</li>')
            s = '%s %s' % (s, htmlPrintItem(v, indent + 1))
    elif isinstance(obj, list):
        s = '%s %s' % (' '*indent, '<ul>\n')
        for v in obj:
            s = '%s %s' % (s, htmlPrintItem(v, indent + 1))
        s = '%s %s %s' % (s, '  ' * indent, '</ul>\n')
    else:
        s = '%s %s %s %s %s' % (s, ' ' * indent, '<li>', str(obj), '</li>')
    return s


def htmlPrintItemList(obj, indent=0):
    s = '%s %s' % (' '*indent, '<ul>\n')
    s = '%s %s' % (s, htmlPrintItem(obj, indent))
    s = '%s %s %s' % (s, '  ' * indent, '</ul>\n')
    return s


def format_response(content_type, data):
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


