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

from handlers import BaseHandler, User

class LoginHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.send_error(403)
        self.render('login.html')

    def post(self):
        login = self.get_body_argument('login', '')
        password = User.password(self.get_body_argument('password', ''))

        sql = 'SELECT name, is_admin FROM users WHERE login = ? AND password = ? LIMIT 1'
        result = self.db.get(sql, login, password)
        if result is not None:
            user = User(login, result.name, result.is_admin)
            self.set_secure_cookie('user', user.serialize())
            return self.redirect(self.get_argument('next', '/'))

        self.alert('Bad credentials')
        self.redirect('/login?user=%s' % login)

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect('/login')
