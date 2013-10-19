import cherrymusicserver as cherry
import time
import os 

from cherrymusicserver import log
from cherrymusicserver import service
from cherrymusicserver import configuration
from cherrymusicserver import userdb 
from cherrymusicserver import metainfo
try:
    from urllib.parse import unquote
except ImportError:
    from backport.urllib.parse import unquote

class RoomSong():
    def __init__(self, path=None, started=None):
        self.started = started if started else time.time()
        if not path:
            self.info = metainfo.MockTag()
        else:
            basedir = cherry.config['media.basedir']
            path = unquote(path)
            if path.startswith('/serve/'):
                path = path[7:]
            elif path.startswith('serve/'):
                path = path[6:]

            self.path = path
            self.abspath = os.path.join(basedir, path)
            self.info = metainfo.getSongInfo(self.abspath)

            self.artist = self.info.artist
            self.album = self.info.album
            self.title = self.info.title
            self.track = self.info.track
            self.length = self.info.length

    def dict(self):
        d = self.info.dict()
        d['path'] = self.path
        d['started'] = self.started
        return d


class RoomMember():
    def __init__(self, user):
        self.uid = user.uid
        self.name = user.name
        self.isadmin = user.isadmin
        self.playlist = None
        self.dj = None

    def dict(self):
        return {
            'uid': self.uid,
            'name': self.name,
            'isadmin': self.isadmin,
            'playlist': self.playlist,
            'dj': self.dj,
        }

@service.user(cache='filecache', 
        model='cherrymodel',
        playlistdb='playlist',
        userdb='users')
class RoomModel:
    def __init__(self, name, message=None):
        self.name = name
        self.message = message
        self.roomsong = RoomSong()
        self.members = []
        self.max_djs = 5 # @todo: add to config: cherry.config['room.max_djs']
        self.current_dj = None


    def next_dj(self):
        djs = self.get_djs()

        if not djs: 
            self.current_dj = None
            return

        if len(djs) == 1:
            self.current_dj = djs[0]
            return

        if self.current_dj:
            next_index = self.current_dj.dj + 1 % self.max_djs
        else:
            next_index = 0

        try:
            self.current_dj = next(user for user in djs if djs.dj == next_index)
        except StopIteration:
            self.current_dj = None


    def get_djs(self):
        djs = [user for user in self.members if user.dj is not None]
        return sorted(djs, key=lambda u: u.dj)


    def find_member(self, uid):
        if not self.members: return None
        try:
            return next(user for user in self.members if user and user.uid == uid)
        except StopIteration:
            return None


    def join(self, uid):
        member = self.find_member(uid)
        if member: return
        user = self.userdb.getUser(uid)
        if user: self.members.append(RoomMember(user))


    def leave(self, uid):
        member = self.find_member(uid)
        if member is None: return
        self.members.remove(member)
        self.reorder_djs()


    def dj(self, uid, plid=None):
        member = self.find_member(uid)
        if member is None: return
        if member.dj is not None: return

        index = max(m.dj for m in self.members)

        if plid:
            member.playlist = plid
        else:
            member.playlist = self.playlistdb.getFirstPlaylistId(uid)

        if index is None:
            member.dj = 0
            self.current_dj = member
            self.next_song()
        else:
            member.dj = index + 1


    def undj(self, uid):
        user = self.find_member(uid)
        if not user: return
        user.dj = None
        self.reorder_djs()


    """ Adjusts the order of the djs """
    def reorder_djs(self):
        dj = 0
        def adjust(user):
            user.dj = dj
            dj += 1
        map(adjust, self.get_djs())


    def select_playlist(self, uid, plid=None):
        user = self.find_member(uid)
        if not user: return
        if plid:
            user.playlist = plid
        else: 
            user.playlist = self.playlist.getFirstPlaylistId(uid)

    """ 
        The room's current song is treated as a property so that
        each time it is requested, its known duration is tested
        againts the passage of time. If it has run past its duration,
        the next song is loaded.
    """
    @property
    def song(self):
        if not self.roomsong.length:
            return self.roomsong
        now = time.time()
        duration = now - self.roomsong.started
        if duration >= self.roomsong.length:
            self.next_song()
        return self.roomsong


    def next_song(self):
        self.next_dj()
        dj = self.current_dj
        if not dj: 
            self.roomsong = RoomSong()
            log.d("No DJs; No songs")
            return
        if not dj.playlist:
            self.undj(dj.uid)
            self.next_song()
            log.d("DJ {0} didn't have a playlist selected. Next.".format(dj.name))
            return
        pl = self.playlistdb.loadPlaylist(dj.playlist, dj.uid)
        if not pl:
            self.undj(dj.uid)
            self.next_song()
            log.d("DJ {0} didn't have any playlist. Next.".format(dj.name))
            return
        self.roomsong = RoomSong(pl[0].path)
        self.playlistdb.popPlaylist(dj.playlist)
        log.d("New song: {0}.".format(pl[0].path))
