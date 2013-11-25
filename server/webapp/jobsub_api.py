import cherrypy
import os

from accounting_group import AccountingGroupsResource
from util import mkdir_p


class Root(object):
    pass


root = Root()
root.acctgroups = AccountingGroupsResource()


def application(environ, start_response):
    os.environ['JOBSUB_INI_FILE'] = environ['JOBSUB_INI_FILE']

    script_name = ''
    appname = environ.get('JOBSUB_APP_NAME')
    if appname is not None:
        script_name = os.path.join('/', appname)
        version = environ.get('JOBSUB_VERSION')
        if version is not None:
            script_name = os.path.join(script_name, appname)
    cherrypy.tree.mount(root, script_name=script_name, config=None)

    log_dir = environ['JOBSUB_LOG_DIR']
    mkdir_p(log_dir)
    access_log = os.path.join(log_dir, 'access.log')
    error_log = os.path.join(log_dir, 'error.log')

    cherrypy.config.update({
        'environment': 'embedded',
        'log.screen': False,
        'log.error_file': error_log,
        'log.access_file': access_log
    })

    return cherrypy.tree(environ, start_response)

if __name__ == '__main__':
    cherrypy.quickstart(root, '/jobsub')
