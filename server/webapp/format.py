import cherrypy
import logger
import json
from functools import wraps, partial
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
        s = '%s%s<li>%s</li>\n' %(s, tabs(dpth),  src)
    return s

def htmlPrintPreformatted(src):
    return """<pre>%s</pre>""" % _htmlPrintPreformatted(src)

def _htmlPrintPreformatted(src, dpth=0, key=''):
    s = ''
    if isinstance(src, dict):
        if key:
            s = '%s%s' % (s,  key)
        for key, value in src.iteritems():
            s = '%s%s' % (s, _htmlPrintPreformatted(value,  key))
    elif isinstance(src, list):
        for litem in src:
            s = '%s%s' % (s, _htmlPrintPreformatted(litem,  key))
    else:
        s = '%s%s' %(s,   src)
    return s

def htmlPrintTableList(src):
    return """<table>%s</table>""" % _htmlPrintTableList(src)

def _htmlPrintTableList(src, dpth=0, key=''):
    s = ''
    if isinstance(src, dict):
        if key:
            s = '%s<tr><td>%s:</td></tr>\n' % (s,  key)
        for key, value in src.iteritems():
            s = '%s%s' % (s, _htmlPrintTableList(value,  key))
    elif isinstance(src, list):
        for litem in src:
            s = '%s%s' % (s, _htmlPrintTableList(litem,  key))
    else:
        s = '%s<tr><td>%s</td></tr>\n' %(s,   src)
    return s

def rel_link(itm,exp=None):
   content_type_accept = cherrypy.request.headers.get('Accept')
   content_type_list = content_type_accept.split(',')
   if 'application/json' in content_type_list:
       return itm
   if 'text/html' not in content_type_list:
       return itm
   if not exp:
      exp = itm
   return "<a href=%s/>%s</a>"%(itm,exp)

def styleSheets():
    bootstrapStyle = """<!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css" integrity="sha512-dTfge/zgoMYpP7QbHy4gWMEGsbsdZeCXz7irItjcC3sPUFtf0kuFbDz/ixG7ArTxmDjLXDmezHubeNikyKGVyQ==" crossorigin="anonymous">

    <!-- Optional theme -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap-theme.min.css" integrity="sha384-aUGj/X2zp5rLCbBxumKTCw2Z50WgIr1vs/PFN4praOTvYXWlVyh2UtNUU0KAUhAX" crossorigin="anonymous">

    <!-- Latest compiled and minified JavaScript -->
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js" integrity="sha512-K1qjQ+NcF2TYO/eI3M6v8EiNYZfA95pQumfvcVrTHtwQVDG+aHRqLi/ETn2uB+1JqwYqVG3LIvdm9lj6imS/pQ==" crossorigin="anonymous"></script>
    """
    fermiStyle="""
    <link href="http://www.fnal.gov/fnalincludes/v6_0/bootstrap/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="http://www.fnal.gov/fnalincludes/v6_0/css/global.css" rel="stylesheet">
    <link href="http://www.fnal.gov/fnalincludes/v6_0/css/legacy.css" rel="stylesheet">
    <link href="http://www.fnal.gov/fnalincludes/v6_0/css/pages.css" rel="stylesheet">
    <link href="http://www.fnal.gov/fnalincludes/v6_0/css/print.css" rel="stylesheet" media="print">
    """
    return fermiStyle

def _format_response(content_type, data, log_response=True):
    logger.log('Response Content-Type: %s' % content_type)
    if log_response:
        #logger.log('Response: %s' % (data))
        pass
    content_type_list = content_type.split(',')
    if 'application/json' in content_type_list:
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return str(json.dumps(data))
    elif 'text/plain' in content_type_list:
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return str(pformat(data))
    elif 'text/html' in content_type_list:
        cherrypy.response.headers['Content-Type'] = 'text/html'
        return '<html><head>%s</head><body>%s</body></html>' % (styleSheets(),htmlPrintItemList(data))
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
        if args[0].__module__ in ('jobsub_help', 'dag_help', 'job', 'jobsub',
                                  'dag', 'condor_commands', 'history', 
                                  'queued_jobs', 'users_jobs','queued_long', 
                                          'queued_dag','sandboxes','summary' ):
            log_response = False

        return _format_response(content_type, data, log_response=log_response)

    return format_response_wrapper
