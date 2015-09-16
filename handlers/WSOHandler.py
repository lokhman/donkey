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

import tornado.websocket
import handlers

class WSOHandler(tornado.websocket.WebSocketHandler):
    clients = set()

    @property
    def db(self):
        return self.application.db

    def get_current_user(self):
        return handlers.BaseHandler.get_user(self)

    def _session(self):
        return (self, self.current_user.login)

    def wso_list():
        pass

    def open(self):
        if self.current_user is None:
            return self.close()

        WSOHandler.clients.add(self._session())

        # player
        self.player = self.application.player

        # initialise
        self.wso = self.application.wso
        self.wso.users()
        self.wso.song()
        self.wso.volume()

    def on_message(self, message):
        if not self.current_user.is_admin:
            return

        try:
            message = message.split(':', 1)
            cmd, args = int(message[0]), []
            if len(message) > 1:
                args = message[1].split('|')

            if cmd == self.wso._IN_SONG:
                self.player.jump(int(args[0]))
            elif cmd == self.wso._IN_PREV:
                self.player.prev()
            elif cmd == self.wso._IN_PLAY:
                self.player.play()
            elif cmd == self.wso._IN_PAUSE:
                self.player.pause()
            elif cmd == self.wso._IN_STOP:
                self.player.stop()
            elif cmd == self.wso._IN_NEXT:
                self.player.next()
            elif cmd == self.wso._IN_POSITION:
                self.player.position = long(args[0])
            elif cmd == self.wso._IN_VOLUME:
                self.player.volume = long(args[0])
                self.wso.volume(args[0])
            elif cmd == self.wso._IN_SHUFFLE:
                self.player.playlist.shuffle()
                self.wso.shuffle()
            elif cmd == self.wso._IN_MOVE:
                self.player.playlist.move(int(args[0]), int(args[1]))
                self.wso.move(args[0], args[1])
            elif cmd == self.wso._IN_TOGGLE:
                enabled = self.player.playlist.toggle(int(args[0]))
                if enabled is not None:
                    sql = 'UPDATE songs SET enabled = ? WHERE id = ?'
                    self.db.execute(sql, enabled, args[0])
                    self.wso.toggle(args[0], enabled)
            elif cmd == self.wso._IN_AFTER:
                self.player.playlist.after(int(args[0]))
                self.wso.after(args[0])
        except: pass

    def on_close(self):
        if self.current_user:
            WSOHandler.clients.remove(self._session())
            self.wso.users()
