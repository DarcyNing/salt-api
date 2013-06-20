
from tornado import web
from tornado import ioloop
from tornado.options import define, options

import app



config = {
    "gzip" : True,
    "debug" : 'DEBUG',
}

urlpatterns = [
    (r"/static/(.*)", web.StaticFileHandler, {"path": "static"}), 
    (r'/',app.Index),
    (r'/login',app.Login),
    (r'/logout',app.Logout),
    (r'/minions',app.Minion),
    (r'/jobs',app.Minion),

] 




if __name__ == '__main__':
    define("bind", default="127.0.0.1", help="bind ip")
    define("port", default="8888", help="listen port")

    options.parse_command_line()
     
    application = web.Application(urlpatterns,**config)
    application.listen(options.port,address=options.bind)
    ioloop.IOLoop.instance().start()


