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
import threading
import subprocess

class LAME(object):
    LAME = 'lame'
    FREQUENCY = 44.1
    BITRATE = 128

    def __init__(self):
        self.queue = []

    def _process(self, callback):
        for args in self.queue:
            try:
                with open(os.devnull, 'w') as buf:
                    p = subprocess.Popen([
                        LAME.LAME,
                        '--quiet',
                        '--mp3input',
                        '-b', str(LAME.BITRATE),
                        '--resample', str(LAME.FREQUENCY),
                        '--ta', args[1],
                        '--tt', args[2],
                        '--tc', 'Donkey',
                        args[0],
                    ], stdout=buf, stderr=buf)
                    p.wait()
                callback(not p.returncode, *args[1:])
            except:
                callback(False, *args[1:])
            finally:
                if os.path.exists(args[0]):
                    os.unlink(args[0])

    def add(self, mp3, artist, title, *args):
        tmpfile = os.path.splitext(mp3)[0]
        if os.path.exists(tmpfile):
            os.unlink(tmpfile)
        os.rename(mp3, tmpfile)
        self.queue.append((tmpfile, artist, title) + args)

    def start(self, callback):
        if self.queue:
            thread = threading.Thread(target=self._process, args=(callback, ))
            thread.daemon = True  # easy killable
            thread.start()
