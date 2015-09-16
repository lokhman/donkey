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

import tornado.web

from handlers import BaseHandler

class ListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        user = None

        login = self.get_argument('user', None)
        if login:
            user = self.db.get('SELECT name FROM users WHERE login = ?', login)
            songs = self.db.query('SELECT id, artist, title, length, enabled '
                'FROM songs WHERE processed = 1 AND user = ? '
                'ORDER BY artist, title', login)
        else:
            songs = self.player.playlist

        if self.is_ajax():
            return self.json(songs)

        self.render('list.html', songs=songs, user=user)
