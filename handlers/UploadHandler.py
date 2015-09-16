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

from handlers import BaseHandler
from utils.lame import LAME
from utils.player import Player

class UploadHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('upload.html')

    @tornado.web.authenticated
    def post(self):
        artists = self.get_body_arguments('artist[]')
        titles = self.get_body_arguments('titles[]')
        mp3s = self.request.files.get('mp3[]', [])

        lame = LAME()
        for i, mp3 in enumerate(mp3s):
            try:
                artist, title = artists[i][:64], titles[i][:128].title()
                if not artist or not title:
                    raise Exception('Song %s should have artist and title' % (i + 1))
                if os.path.splitext(mp3['filename'])[1].lower() != '.mp3':
                    raise Exception('Song %s should have MP3 format' % (i + 1))

                sql = 'INSERT INTO songs (user, artist, title) VALUES (?, ?, ?)'
                song_id = self.db.execute(sql, self.current_user.login, artist, title)

                path = Player.song2path(song_id)
                with open(path, 'wb') as fp:
                    fp.write(mp3['body'])

                lame.add(path, artist, title, song_id, path)
            except ValueError:
                return self.send_error(400)
            except Exception as e:
                self.alert(e)

        if not lame.queue:
            return self.redirect('/upload')

        def callback(success, artist, title, song_id, path):
            if success:
                try:
                    # read mp3
                    mf = Player.open(path)
                    length = mf.total_time()

                    sql = 'UPDATE songs SET length = ?, bitrate = ?, samplerate = ?, processed = 1 WHERE id = ?'
                    self.db.execute(sql, length, mf.bitrate() / 1000, mf.samplerate(), song_id)

                    # update lists
                    self.player.playlist.append(song_id, artist, title, length)
                    self.application.wso.new(song_id)

                    # update free space
                    self.application.disk = self.player.free_space()
                    self.application.wso.disk(self.application.disk)

                    message = u'Song "%s \u2014 %s" was added to the playlist' % (artist, title)
                    return self.alert(message, self.ALERT_SUCCESS)
                except: pass

            self.db.execute('DELETE FROM songs WHERE id = ?', song_id)
            self.alert(u'File for song "%s \u2014 %s" is broken' % (artist, title))

        lame.start(callback)

        total = len(lame.queue)
        self.alert('%s song%s uploaded, now processing...' %
            (total, ' was' if total == 1 else 's were'), self.ALERT_INFO)

        self.redirect('/upload')
