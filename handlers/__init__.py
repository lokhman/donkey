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

import os
import psutil
import hashlib
import cPickle
import threading
import functools
import tornado.web
import tornado.escape

from handlers.WSOHandler import WSOHandler

class BaseHandler(tornado.web.RequestHandler):
    ALERT_SUCCESS = 'success'
    ALERT_WARNING = 'warning'
    ALERT_DANGER = 'danger'
    ALERT_INFO = 'info'

    @staticmethod
    def get_user(handler):
        return User().unserialize(handler.get_secure_cookie('user'))

    @staticmethod
    def restricted(method):
        @tornado.web.authenticated
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if not self.current_user.is_admin:
                return self.send_error(403)
            return method(self, *args, **kwargs)
        return wrapper

    @property
    def db(self):
        return self.application.db

    @property
    def player(self):
        return self.application.player

    @property
    def alerts(self):
        if self.current_user:
            return self.application.alerts.list(self.current_user.login)

        def generator(cookie):
            try:
                yield cPickle.loads(cookie)
            except:
                raise StopIteration
            finally:
                self.clear_cookie('alert')

        return generator(self.get_secure_cookie('alert'))

    def alert(self, message, status=ALERT_DANGER):
        if self.current_user:
            self.application.alerts.push(self.current_user.login,
                unicode(message), status)
        else:
            self.set_secure_cookie('alert',
                cPickle.dumps((unicode(message), status), cPickle.HIGHEST_PROTOCOL))

    def initialize(self):
        pass

    def get_current_user(self):
        return BaseHandler.get_user(self)

    def is_ajax(self):
        return self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    def json(self, chunk):
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(tornado.escape.json_encode(chunk))

class Alert(object):
    def __init__(self):
        self.alerts = dict()

    def push(self, login, message, status):
        if login not in self.alerts:
            self.alerts[login] = list()
        self.alerts[login].append((message, status))

    def list(self, login):
        if login not in self.alerts:
            raise StopIteration
        for alert in self.alerts[login]:
            yield alert
        del self.alerts[login]

class User(object):
    def __init__(self, login=None, name=None, is_admin=False):
        self.login = login
        self.name = name
        self.is_admin = bool(is_admin)

    def __str__(self):
        return self.name

    @staticmethod
    def password(password):
        return hashlib.sha1(password).hexdigest()

    def serialize(self):
        return cPickle.dumps((self.login, self.name, self.is_admin), cPickle.HIGHEST_PROTOCOL)

    def unserialize(self, serialized):
        try:
            self.login, self.name, self.is_admin = cPickle.loads(serialized)
            return self
        except: return None

class WSO(object):
    _OUT_LIST = 0x01
    _OUT_USERS = 0x02
    _OUT_SONG = 0x03
    _OUT_POSITION = 0x04
    _OUT_VOLUME = 0x05
    _OUT_NEW = 0x06
    _OUT_MOVE = 0x07
    _OUT_SHUFFLE = 0x08
    _OUT_DISK = 0x09
    _OUT_MEMCPU = 0x0A
    _OUT_TOGGLE = 0x0B
    _OUT_AFTER = 0x0C

    _IN_SONG = 0x11
    _IN_PREV = 0x12
    _IN_PLAY = 0x13
    _IN_PAUSE = 0x14
    _IN_STOP = 0x15
    _IN_NEXT = 0x16
    _IN_POSITION = 0x17
    _IN_VOLUME = 0x18
    _IN_SHUFFLE = 0x19
    _IN_MOVE = 0x1A
    _IN_TOGGLE = 0x1B
    _IN_AFTER = 0x1C

    def __init__(self, player):
        # set events
        player.on_play = self.song
        player.on_stop = lambda: self.position(0L)

        self._player = player
        self._queue = []
        self._ticks = 0
        self._ticker()

    @staticmethod
    def commands():
        cc = filter(lambda x: x[:2] in ('_I', '_O'), dir(WSO))
        return { c: getattr(WSO, c) for c in cc }

    def _ticker(self):
        if self._player.is_playing:
            self.position(self._player.position)

        if self._ticks % 4 == 0:
            try:
                # memcpu each 2 secs
                self.memcpu()
            except: pass

        thread = threading.Thread(target=self._stream)
        thread.daemon = True
        thread.start()

    def _stream(self):
        for client in WSOHandler.clients:
            for message in self._queue:
                client[0].write_message(message)
        del self._queue[:]

        # ticks
        self._ticks += 1
        if self._ticks > 99:
            self._ticks = 0

        # timer
        threading.Timer(0.5, self._ticker).start()

    def _out(self, cmd, *args):
        self._queue.append('%s:%s' % (cmd, '|'.join(map(str, args))))

    def list(self):
        return self._out(WSO._OUT_LIST)

    def new(self, song_id):
        self._out(WSO._OUT_NEW, song_id)

    def move(self, song_id, position):
        return self._out(WSO._OUT_MOVE, song_id, position)

    def shuffle(self):
        return self._out(WSO._OUT_SHUFFLE)

    def users(self):
        self._out(WSO._OUT_USERS, *set(x[1] for x in WSOHandler.clients))

    def song(self, song_id=None, length=None):
        if song_id is None or length is None:
            current = self._player.current
            if current:
                self.song(current[0], current[3])
            return
        self._out(WSO._OUT_SONG, song_id, length)

    def position(self, position):
        self._out(WSO._OUT_POSITION, position)

    def volume(self, volume=None):
        if volume is None:
            return self.volume(self._player.volume)
        self._out(WSO._OUT_VOLUME, volume)

    def disk(self, disk):
        self._out(WSO._OUT_DISK, disk)

    def memcpu(self):
        mem, cpu = self._player.memcpu()
        self._out(WSO._OUT_MEMCPU, mem, cpu)

    def toggle(self, song_id, enabled):
        self._out(WSO._OUT_TOGGLE, song_id, int(enabled))

    def after(self, song_id):
        self._out(WSO._OUT_AFTER, song_id)
