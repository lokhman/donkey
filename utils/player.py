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
import mad
import random
import psutil
import alsaaudio
import threading

class Player(object):
    MEDIA = '/app/donkey/media'
    VOLUME_PAD = 50

    def __init__(self, playlist):
        self.is_playing = False
        self.current = None

        self._playlist = playlist
        self._thread = None
        self._mf = None

        self._ao_init()

    @staticmethod
    def song2path(song_id):
        name = '%07d' % (int(song_id) / 100)
        path = os.path.join(Player.MEDIA, name)
        try:
            os.mkdir(path)
        except: pass
        return os.path.join(path, '%07d.mp3' % song_id)

    @staticmethod
    def fmt_bytes(size, p=2):
        if size == 1:
            return '1 byte'
        ranges = (
            (1 << 50L, 'PB'),
            (1 << 40L, 'TB'),
            (1 << 30L, 'GB'),
            (1 << 20L, 'MB'),
            (1 << 10L, 'kB'),
            (1, 'bytes'),
        )
        for f, s in ranges:
            if size >= f: break
        return '%.*f %s' % (p, size / float(f), s)

    @staticmethod
    def free_space():
        du = psutil.disk_usage(Player.MEDIA)
        return '%s (%s%%)' % (Player.fmt_bytes(du.free), 100 - du.percent)

    @staticmethod
    def memcpu():
        return (psutil.virtual_memory().percent, psutil.cpu_percent())

    @staticmethod
    def open(path):
        return mad.MadFile(path)

    @property
    def playlist(self):
        return self._playlist

    @property
    def position(self):
        if self._mf:
            return self._mf.current_time()
        return 0L

    @position.setter
    def position(self, position):
        try:
            self._mf.seek_time(position)
        except: pass

    @property
    def volume(self):
        channels = self._mixer.getvolume()
        return sum(channels) / len(channels)

    @volume.setter
    def volume(self, volume):
        if Player.VOLUME_PAD <= volume <= 100:
            self._mixer.setvolume(volume)

    def _ao_init(self):
        if getattr(self, '_audio', None):
            self._audio.close()
        self._audio = alsaaudio.PCM()

        if getattr(self, '_mixer', None):
            self._mixer.close();
        self._mixer = alsaaudio.Mixer('PCM')

    def _ao_write(self, buf):
        try:
            self._audio.write(buf)
        except:
            self._ao_init()
            self._ao_write(buf)

    def _wait(self, callback):
        if self._thread:
            while self._thread.is_alive():
                pass  # wait
        callback()

    def _stream(self):
        while self._mf and self.is_playing:
            buf = self._mf.read()
            if not buf:
                self.is_playing = False
                self._thread = None  # memleak?
                return self.next()
            self._ao_write(buf)
        self.is_playing = False

    def play(self):
        if self.is_playing:
            return

        # protect threads
        if self._thread and self._thread.is_alive():
            return

        if self._mf is None:
            try:
                self.current = self._playlist.current
                path = Player.song2path(self.current[0])
                self._mf = Player.open(path)

                # trigger event
                self.on_play()
            except: return

        self.is_playing = True

        # start streaming
        self._thread = threading.Thread(target=self._stream)
        self._thread.daemon = True  # easy killable
        self._thread.start()

    def pause(self):
        self.is_playing = False

    def next(self):
        self._mf = None
        self._playlist.next()
        self._wait(self.play)

    def prev(self):
        self._mf = None
        self._playlist.prev()
        self._wait(self.play)

    def stop(self):
        self._mf = None

        # trigger event
        self.on_stop()

    def jump(self, song_id):
        index = self._playlist.index(song_id)
        if index is not None:
            self._playlist.current = index
            self._mf = None
            self._wait(self.play)

    def remove(self, song_id):
        if self.current and self.current[0] == song_id:
            if self.is_playing:
                return False
            self._mf = None

        try:
            self._playlist.remove(song_id)
            os.remove(Player.song2path(song_id))
            return True
        except:
            return False

    def on_play(self):
        # on_play event
        pass

    def on_stop(self):
        # on_stop event
        pass

class Playlist(list):
    def __init__(self, *args, **kwargs):
        super(Playlist, self).__init__(*args, **kwargs)
        self._current = 0

    def __iter__(self):
        keys = ('id', 'artist', 'title', 'length', 'enabled')
        return (dict(zip(keys, x)) for x in list.__iter__(self))

    @property
    def current(self):
        if len(self) == 0:
            return None

        return self[self._current]

    @current.setter
    def current(self, current):
        if 0 <= current < len(self):
            self._current = current

    def append(self, song_id, artist, title, length, enabled=True):
        super(Playlist, self).append((song_id, artist, title, length, enabled))

    def index(self, song_id):
        for i, song in enumerate(self):
            if song_id == song.get('id'):
                return i
        return None

    def remove(self, song_id):
        index = self.index(song_id)

        del self[index]
        if index < self._current:
            self._current -= 1
        elif index == self._current:
            self._current = 0

    def prev(self):
        length = len(self)
        if length == 0:
            return None

        self._current -= 1
        if self._current < 0:
            self._current = length - 1

        current = self.current
        if not current[-1]:
            if any(map(lambda x: x.get('enabled'), self)):
                return self.prev()

        return current

    def next(self):
        length = len(self)
        if length == 0:
            return None

        self._current += 1
        if self._current > length - 1:
            self._current = 0

        current = self.current
        if not current[-1]:
            if any(map(lambda x: x.get('enabled'), self)):
                return self.next()

        return current

    def shuffle(self, index=None):
        if index is None:
            index = self._current + 1

        buf = self[index:]
        random.shuffle(buf)
        del self[index:]

        super(Playlist, self).__init__(self[:index] + buf)

    def move(self, song_id, position):
        index = self.index(song_id)
        if index is None:
            return

        current = self.current
        self.insert(position, self.pop(index))
        if current:
            self._current = self.index(current[0])

    def toggle(self, song_id):
        index = self.index(song_id)
        if index is None:
            return

        enabled = not self[index][-1]
        self[index] = self[index][:-1] + (enabled, )

        return enabled

    def after(self, song_id):
        index = self.index(song_id)
        if index is None:
            return

        if index < self._current:
            self.move(song_id, self._current)
        elif index > self._current:
            self.move(song_id, self._current + 1)
