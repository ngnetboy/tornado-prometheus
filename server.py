from tornado.web import Application
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from supernms import urlmap
from tornado.options import define, options, parse_command_line


def runserver():
    app = Application(
        handlers = urlmap.urlpattern,
    )

    define('port', default=9696, help='run on the given port', type=int)

    parse_command_line()

    http_server = HTTPServer(app, xheaders = True)
    http_server.listen(options.port)
    IOLoop.current().start()

if __name__ == "__main__":
    runserver()
