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

class SongHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, song_id):
        song = self.db.get('SELECT s.*, COALESCE(u.name, s.user) user FROM songs s '
            'LEFT JOIN users u ON u.login = s.user WHERE id = ?', song_id)
        if not song:
            return self.send_error(404)

        if self.is_ajax():
            return self.json(song)

        if not self.current_user.is_admin:
            return self.send_error(403)

        self.render('song.html', song=song)

    @BaseHandler.restricted
    def post(self, song_id):
        # on song delete
        if 'delete' in self.request.body_arguments:
            try:
                if not self.player.remove(int(song_id)):
                    raise
                self.application.wso.list()

                self.db.execute('DELETE FROM songs WHERE id = ?', song_id)
                self.alert('Song #%s was successfully removed' % song_id, self.ALERT_WARNING)
            except:
                self.alert('Song #%s cannot be removed' % song_id)

            return self.redirect('/')

        # on song update
        artist = self.get_argument('artist')
        title = self.get_argument('title')
        try:
            self.db.execute('UPDATE songs SET artist = ?, title = ? WHERE id = ?', artist, title, song_id)

            index = self.player.playlist.index(int(song_id))
            song = self.player.playlist[index]
            self.player.playlist[index] = (song[0], artist, title, song[3], song[4])
            self.application.wso.list()

            self.alert('Details for song #%s were successfully updated' % song_id, self.ALERT_SUCCESS)
            self.redirect('/')
        except:
            self.alert('Details for song #%s cannot be updated' % song_id)
            self.redirect('/songs/%s' % song_id)
