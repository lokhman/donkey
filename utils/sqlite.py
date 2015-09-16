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

import sqlite3
import itertools

class SQLite(object):
    class Row(dict):
        def __getattr__(self, key):
            try:
                return self[key]
            except KeyError:
                raise AttributeError(key)

    def __init__(self, filename, db=None):
        self._filename = filename
        self._db = db

    def __del__(self):
        self._close()

    def _connect(self):
        self._db = sqlite3.connect(self._filename)
        self._db.isolation_level = None

    def _close(self):
        if self._db is not None:
            self._db.close()
            self._db = None

    def _cursor(self):
        if self._db is None:
            self._connect()
        return self._db.cursor()

    def execute(self, query, *args):
        try:
            cursor = self._cursor()
            cursor.execute(query, args)
            self._db.commit()
            return cursor.lastrowid
        except:
            self._db.rollback()
            raise
        finally:
            self._close()

    def query(self, query, *args):
        try:
            cursor = self._cursor()
            cursor.execute(query, args)
            columns = [c[0] for c in cursor.description]
            return [SQLite.Row(itertools.izip(columns, row)) for row in cursor]
        finally:
            self._close()

    def get(self, query, *args):
        rows = self.query(query, *args)
        if not rows:
            return None
        elif len(rows) > 1:
            raise Exception('Multiple rows returned from sqlite.get() query')
        return rows[0]

    def scalar(self, query, *args):
        return self.get(query, *args).itervalues().next()
