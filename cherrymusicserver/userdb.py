#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 Tom Wallroth & Tilman Boerner
#
# Project page:
#   http://fomori.org/cherrymusic/
# Sources on github:
#   http://github.com/devsnd/cherrymusic/
#
# CherryMusic is based on
#   jPlayer (GPL/MIT license) http://www.jplayer.org/
#   CherryPy (BSD license) http://www.cherrypy.org/
#
# licensed under GNU GPL version 3 (or later)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#

import hashlib
import uuid

from collections import namedtuple

from cherrymusicserver import database
from cherrymusicserver import log
from cherrymusicserver import service
from cherrymusicserver.database.connect import BoundConnector

DBNAME = 'user'
FIELDS = ['rowid', 'username', 'admin', 'realname', 'avatar_url', 'public_url', 'points', 'password', 'salt']
FIELDLIST = ", ".join(FIELDS)

class UserDB:
    def __init__(self, connector=None):
        database.require(DBNAME, version='2')
        self.conn = BoundConnector(DBNAME, connector).connection()

    def addUser(self, username, password, admin):
        if not (username.strip() or password.strip()):
            log.d('empty username or password!')
            return
        user = User.create(username, password, admin)
        self.conn.execute('''
        INSERT INTO users
        (username, admin, password, salt)
        VALUES (?,?,?,?)''',
        (user.name, 1 if user.isadmin else 0, user.password, user.salt))
        self.conn.commit()
        msg = 'added user: ' + user.name
        log.d(msg)
        return msg

    def isDeletable(self, userid):
        #cant delete 1st admin
        if not userid == 1:
            return True
        return False

    def changePassword(self, username, newpassword):
        if not newpassword.strip():
            return "not a valid password"
        else:
            newuser = User.create(username, newpassword, False) #dummy user for salt
            self.conn.execute('''
            UPDATE users SET password = ?, salt = ? WHERE username = ?
            ''', (newuser.password, newuser.salt, newuser.name) )
            return "success"

    def deleteUser(self, userid):
        if self.isDeletable(userid):
            self.conn.execute('''DELETE FROM users WHERE rowid = ?''', (userid,))
            self.conn.commit()
            return True
        return False

    def savePoints(self, uid, points):
        self.conn.execute("UPDATE users SET points = ? WHERE rowid = ?", (points, uid))
        self.conn.commit()

    def auth(self, username, password, create=True):
        '''try to authenticate the given username and password. on success,
        a valid user tuple will be returned; failure will return User.nobody().
        will fail if username or password are empty.'''

        if not (username.strip() and password.strip()):
            return User.nobody()

        rows = self.conn.execute('SELECT ' + FIELDLIST + 
                                 ' FROM users WHERE username = ?', (username,))\
                                 .fetchall()
        assert len(rows) <= 1
        if rows:
            user = User._make(rows[0])
            if Crypto.scramble(password, user.salt) == user.password:
                return user
        elif create:
            log.i("Creating user '{0}'".format(username))
            self.addUser(username, password, False)
            return self.auth(username, password, False)

        return User.nobody()

    def getUserList(self):
        cur = self.conn.cursor()
        cur.execute('''SELECT rowid, username, admin FROM users''')
        ret = []
        for uid, user, admin in cur.fetchall():
            ret.append({'id':uid, 'username':user, 'admin':admin,'deletable':self.isDeletable(uid)})
        return ret

    def getUser(self, userid):
        res = self.conn.execute("SELECT " + FIELDLIST + " FROM users WHERE rowid = ?", (userid,))
        row = res.fetchone()
        if not row: return User.nobody()
        user = User._make(row).withoutAuth()
        return user

    def getUserCount(self):
        cur = self.conn.cursor()
        cur.execute('''SELECT COUNT(*) FROM users''')
        return cur.fetchall()[0][0]

    def getNameById(self, userid):
        res = self.conn.execute('''SELECT username FROM users WHERE rowid = ?''',(userid,))
        username = res.fetchone()
        return username[0] if username else 'nobody'

class Crypto(object):

    @classmethod
    def generate_salt(cls):
        '''returns a random hex string'''
        return uuid.uuid4().hex

    @classmethod
    def salted(cls, plain, salt):
        '''interweaves plain and salt'''
        return (plain[1::2] + salt + plain[::2])[::-1]

    @classmethod
    def scramble(cls, plain, salt):
        '''returns a sha512-hash of plain and salt as a hex string'''
        saltedpassword_bytes = cls.salted(plain, salt).encode('UTF-8')
        return hashlib.sha512(saltedpassword_bytes).hexdigest()


class User(namedtuple('User_', FIELDLIST)):

    __NOBODY = None

    @property
    def isadmin(self):
        return self.admin

    @property
    def name(self):
        return self.username

    @property
    def uid(self):
        return self.rowid

    def withoutAuth(self):
        return self._replace(password=None, salt=None)

    def __new__(self, *args, **kwargs):
        values = []
        for field in FIELDS:
            values.append(kwargs.get(field, None))
        return super(User, self).__new__(self, *values)

    @classmethod
    def create(cls, name, password, isadmin=False):
        '''create a new user with given name and password.
        will add a random salt.'''

        if not name.strip():
            raise ValueError('name must not be empty')
        if not password.strip():
            raise ValueError('password must not be empty')

        salt = Crypto.generate_salt()
        password = Crypto.scramble(password, salt)
        return User(rowid=-1, username=name, admin=isadmin, password=password, salt=salt)


    @classmethod
    def nobody(cls):
        '''return a user object representing an unknown user'''
        if User.__NOBODY is None:
            User.__NOBODY = User(rowi=-1, username=None, admin=None, password=None, salt=None)
        return User.__NOBODY
