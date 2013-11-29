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

from cherrymusicserver import database
from cherrymusicserver import log
from cherrymusicserver import service
from cherrymusicserver.cherrymodel import MusicEntry
from cherrymusicserver.database.connect import BoundConnector
try:
    from urllib.parse import unquote
except ImportError:
    from backport.urllib.parse import unquote

DBNAME = 'playlist'

class PlaylistDB:
    def __init__(self, connector=None):
        database.require(DBNAME, version='1')
        self.conn = BoundConnector(DBNAME, connector).connection()

    def deletePlaylist(self, plid, userid, override_owner=False):
        cursor = self.conn.cursor()
        ownerid = cursor.execute(
            "SELECT userid FROM playlists WHERE rowid = ?", (plid,)).fetchone()
        if not ownerid:
            return "This playlist doesn't exist! Nothing deleted!"
        if userid != ownerid[0] and not override_owner:
            return "This playlist belongs to another user! Nothing deleted."
        cursor.execute("""DELETE FROM playlists WHERE rowid = ?""", (plid,))
        self.conn.commit()
        return 'success'

    def addSong(self, uid, plid, song):
        cursor = self.conn.cursor()
        cursor.execute("""SELECT rowid FROM playlists WHERE
            rowid = ? AND (public = 1 OR userid = ?) LIMIT 0,1""",
            (plid, uid));
        playlist = cursor.fetchone()
        if not playlist: return []
        """ Shift everything down by 1 to make room """
        cursor.execute("UPDATE tracks SET track = track + 1 WHERE playlistid = ?", (plid,))
        """ Add the new song to the top """
        cursor.execute("""INSERT INTO tracks (playlistid, track, url, title)
            VALUES (?,?,?,?)""", (plid, 0, song['urlpath'], song['label']))
        self.conn.commit()
        return self.loadPlaylist(plid, uid)

    def removeSong(self, uid, plid, song):
        cursor = self.conn.cursor()
        cursor.execute("""SELECT rowid FROM playlists WHERE
            rowid = ? AND (public = 1 OR userid = ?) LIMIT 0,1""",
            (plid, uid));
        playlist = cursor.fetchone()
        if not playlist: return []
        """ Get rid of """
        cursor.execute("""DELETE FROM tracks WHERE playlistid = ? AND track = ? AND url = ?""", 
                (plid, song['track'], song['urlpath']))
        """ Shift everything back by one now that there's room """
        cursor.execute("UPDATE tracks SET track = track - 1 WHERE playlistid = ? AND track > ?", 
                (plid, song['track']))
        self.conn.commit()
        return self.loadPlaylist(plid, uid)

    def savePlaylist(self, userid, public, playlisttitle, playlistid=None):
        cursor = self.conn.cursor()
        # Verify that the user owns the playlist
        if playlistid: 
            cursor.execute("""SELECT rowid FROM playlists
                WHERE userid = ? AND rowid = ?""", (userid, playlistid))
            if not cursor.fetchone():
                log.d("User {0} does not own {1}".format(userid, playlistid))
                return None 

        # Verify that the title is unique for the user
        cursor.execute("""SELECT rowid FROM playlists
            WHERE userid = ? AND title = ?""", (userid, playlisttitle))
        titleid = cursor.fetchone()
        if titleid:
            log.d("User {0} already has playlist {1}".format(userid, playlisttitle))
            playlistid = titleid[0]

        public = bool(public)

        if not playlistid:
            cursor.execute("""INSERT INTO playlists
                (title, userid, public) VALUES (?,?,?)""",
                (playlisttitle, userid, public))
            log.d("User {0} created new playlist {1}".format(userid, playlisttitle))
            playlistid = cursor.lastrowid
        else:
            cursor.execute("""UPDATE playlists
                SET title = ?, public = ? WHERE rowid = ? AND userid = ?""",
                (playlisttitle, public, playlistid, userid))

        self.conn.commit()
        log.d("Done saving playlist {0}".format(playlisttitle))
        return {
            "plid"   : int(playlistid),
            "title"  : playlisttitle,
            "public" : public,
            "userid" : userid,
            "owner"  : 1,
        }


    def loadPlaylist(self, playlistid, userid, limit=None):
        cursor = self.conn.cursor()
        sql = "SELECT rowid FROM playlists WHERE rowid = ? AND (public = 1 OR userid = ?) LIMIT 0,1"
        cursor.execute(sql, (playlistid, userid));
        result = cursor.fetchone()
        if not result:
            log.i("Could not find playlist {0} for user id {1}".format((playlistid, userid)))
            return None
        sql = "SELECT title, url FROM tracks WHERE playlistid = ? ORDER BY track ASC"
        if limit: sql += " LIMIT 0," + str(limit)
        cursor.execute(sql, (playlistid,))
        alltracks = cursor.fetchall()
        if not alltracks:
            log.i("No songs in playlist {0}".format(playlistid))
            return None
        apiplaylist = []
        for track in alltracks:
            #TODO ugly hack: playlistdb saves the "serve" dir as well...
            trackurl = unquote(track[1])
            if trackurl.startswith('/serve/'):
                trackurl = trackurl[7:]
            elif trackurl.startswith('serve/'):
                trackurl = trackurl[6:]
            apiplaylist.append(MusicEntry(path=trackurl, repr=unquote(track[0])))
        return apiplaylist

    def getName(self, plid, userid ):
        cur = self.conn.cursor()
        cur.execute("""SELECT rowid as id,title FROM playlists WHERE
            (public = 1 OR userid = ?) and rowid=?""", (userid,plid));
        result = cur.fetchall()
        if result:
            print(result)
            return result[0][1]
        return 'playlist'

    def setPublic(self, userid, plid, value):
        ispublic = 1 if value else 0
        cur = self.conn.cursor()
        cur.execute("""UPDATE playlists SET public = ? WHERE rowid = ? AND userid = ?""", (ispublic, plid, userid))

    def showPlaylists(self, userid):
        cur = self.conn.cursor()
        #change rowid to id to match api
        cur.execute("""SELECT rowid as id, title, userid, public FROM playlists WHERE
            public = 1 OR userid = ?""", (userid,))
        res = cur.fetchall()
        return list(map(lambda x: {'plid':x[0], 'title':x[1], 'userid':x[2],'public':bool(x[3]), 'owner':bool(userid==x[2])}, res))

    def getFirstPlaylistId(self, userid):
        cur = self.conn.cursor()
        cur.execute("""SELECT playlists.rowid FROM playlists 
            JOIN tracks ON (playlists.rowid = tracks.playlistid) 
            WHERE userid = ? OR public = 1 LIMIT 0, 1""", (userid,))
        res = cur.fetchone()
        return res[0] if res else None

    """ Moves the first playlist track to the last """
    def popPlaylist(self, plid):
        cur = self.conn.cursor()
        cur.execute("UPDATE tracks SET track = track - 1 WHERE playlistid = ?", (plid,))
        cur.execute("SELECT MAX(track) FROM tracks WHERE playlistid = ?", (plid,))
        max = cur.fetchone()
        if max:
            cur.execute("UPDATE tracks SET track = ? WHERE track = -1 AND playlistid = ?", (max[0] + 1, plid))

    def createPLS(self,userid,plid, addrstr):
        pl = self.loadPlaylist(userid, plid)
        if pl:
            plsstr = '''[playlist]
    NumberOfEntries={}
    '''.format(len(pl))
            for i,track in enumerate(pl):
                trinfo = {  'idx':i+1,
                            'url':addrstr+'/serve/'+track.path,
                            'name':track.repr,
                            'length':-1,
                        }
                plsstr += '''
    File{idx}={url}
    Title{idx}={name}
    Length{idx}={length}
    '''.format(**trinfo)
            return plsstr

    def createM3U(self,userid,plid,addrstr):
        pl = self.loadPlaylist(userid, plid)
        if pl:
            trackpaths = map(lambda x: addrstr+'/serve/'+x.path,pl)
            return '\n'.join(trackpaths)


