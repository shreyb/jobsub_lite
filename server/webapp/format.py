import cherrypy
import json

from pprint import pformat


def htmlPrintItems(dictObj, indent=0):
    s = '%s %s' % (' '*indent, '<ul>\n')
    for k, v in dictObj.iteritems():
        if isinstance(v, dict):
            s = '%s %s %s %s %s %s' % (s, '  '*indent, '<li>', str(k), ':', '</li>')
            s = '%s %s' % (s, htmlPrintItems(v, indent+1))
        else:
            s = '%s %s %s %s %s %s %s' % (s, ' '*indent, '<li>', str(k), ':', str(v), '</li>')
    s = '%s %s %s' % (s, '  '*indent, '</ul>\n')
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
        return '<html><body>%s</body></html>' % htmlPrintItems(data)
    else:
        return 'Content type %s not supported' % content_type


