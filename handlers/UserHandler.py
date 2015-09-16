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

from handlers import BaseHandler, User

class UserHandler(BaseHandler):
    @BaseHandler.restricted
    def get(self, login=None):
        user = User(login or '', '', '')
        if login:
            sql = 'SELECT name, is_admin FROM users WHERE login = ?'
            result = self.db.get(sql, login)
            try:
                user.name = result.name
                user.is_admin = result.is_admin
            except:
                return self.send_error(404)

        self.render('user.html', user=user)

    @BaseHandler.restricted
    def post(self, login=None):
        # fool proof protection :)
        if self.current_user.login != 'admin' and login == 'admin':
            return self.send_error(405)

        # on user delete
        if 'delete' in self.request.body_arguments:
            try:
                if not login or login == self.current_user.login:
                    raise

                self.db.execute('DELETE FROM users WHERE login = ?', login)
                self.alert('User "%s" was successfully removed' % login, self.ALERT_WARNING)
            except:
                self.alert('User "%s" cannot be removed' % login)

            return self.redirect('/users')

        # on user upsert
        name = self.get_argument('name')
        password = self.get_argument('password', '')
        is_admin = bool(self.get_argument('is_admin', False))
        if not login:
            login = self.get_argument('login')
            try:
                if not password:
                    raise

                sql = 'INSERT INTO users (login, password, name, is_admin) VALUES (?, ?, ?, ?)'
                self.db.execute(sql, login, User.password(password), name, is_admin)
                self.alert('User "%s" was successfully created' % login, self.ALERT_SUCCESS)
                return self.redirect('/users/%s' % login)
            except:
                self.alert('User "%s" cannot be created' % login)
                return self.redirect('/users')

        if password:
            sql = 'UPDATE users SET password = ?, name = ?, is_admin = ? WHERE login = ?'
            args = [User.password(password), name, is_admin, login]
        else:
            sql = 'UPDATE users SET name = ?, is_admin = ? WHERE login = ?'
            args = [name, is_admin, login]

        try:
            self.db.execute(sql, *args)
            self.alert('Details for user "%s" were successfully updated' % login, self.ALERT_SUCCESS)
        except:
            self.alert('Details for user "%s" cannot be updated' % login)

        self.redirect('/users/%s' % login)
