#!/usr/bin/env python
#
# This code is part of Donkey project.
#
# Copyright (c) 2014 Alexander Lokhman <alex.lokhman@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Created on August 2014

import os.path
import tornado.web
import tornado.ioloop

from datetime import datetime
from tornado.options import define, options, parse_command_line

from handlers import Alert, WSO
from handlers.MainHandler import MainHandler
from handlers.LoginHandler import LoginHandler, LogoutHandler
from handlers.UploadHandler import UploadHandler
from handlers.SongHandler import SongHandler
from handlers.UserHandler import UserHandler
from handlers.ListHandler import ListHandler
from handlers.WSOHandler import WSOHandler

from utils.sqlite import SQLite
from utils.player import Player, Playlist

define('port', default=8080, help='Run on the given port', type=int)
define('debug', default=False, help='Run in debug mode', type=bool)
define('db', default='data/donkey.db', help='File with Donkey SQLite database')

class Application(tornado.web.Application):
    def __init__(self):
        self.version = 1.27
        self.uptime = datetime.now()

        # free disk space
        self.disk = Player.free_space()

        # initialise database
        self.db = SQLite(options.db)

        # initialise alerts
        self.alerts = Alert()

        # initialise playlist
        sql = 'SELECT id, artist, title, length, enabled FROM songs WHERE processed = 1 ORDER BY RANDOM()'
        self.playlist = Playlist((x.id, x.artist, x.title, x.length, x.enabled) for x in self.db.query(sql))

        # initialise player
        self.player = Player(self.playlist)

        # initialise WSO
        self.wso = WSO(self.player)

        # initialise application
        super(Application, self).__init__(
            [
                (r'/', MainHandler),
                (r'/login', LoginHandler),
                (r'/logout', LogoutHandler),
                (r'/upload', UploadHandler),
                (r'/songs/(\d+)', SongHandler),
                (r'/users(?:/([^/]+))?', UserHandler),
                (r'/list', ListHandler),
                (r'/wso', WSOHandler),
            ],
            login_url='/login',
            cookie_secret='xWP6dkmS489K14Uaj16w416P8Y7b2L474807tjwJ',
            template_path=os.path.join(os.path.dirname(__file__), 'templates'),
            static_path=os.path.join(os.path.dirname(__file__), 'static'),
            debug=options.debug,
            xsrf_cookies=True,
            gzip=True,
        )

if __name__ == '__main__':
    parse_command_line()
    Application().listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
