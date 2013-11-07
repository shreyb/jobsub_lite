import cherrypy


class Experiments(object):

    exposed = True

    def GET(self, *args, **kwargs):
        pass

    def PUT(self, *args, **kwargs):
        pass

    def POST(self, *args, **kwargs):
        print args
        print kwargs

    def DELETE(self, *args, **kwargs):
        pass
