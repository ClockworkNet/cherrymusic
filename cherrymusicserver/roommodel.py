import cherrymusicserver as cherry
import time

from cherrymusicserver import log
from cherrymusicserver import service
from cherrymusicserver import configuration
from cherrymusicserver import userdb 

@service.user(cache='filecache', 
        model='cherrymodel',
        playlistdb='playlist',
        userdb='users')
class RoomModel:
    def __init__(self, name, message=None):
        self.name = name
        self.message = message

        self.track = None
        self.track_start = None

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

        self.current_dj = next(user for user in djs if djs.dj == next_index)
        return self.current_dj


    def get_djs(self):
        djs = [user for user in self.members if user.dj is not None]
        return sorted(djs, key=lambda u: u.dj)


    def find_user_in_room(self, uid):
        if not self.members: return None
        try:
            return next(user for user in self.members if user and user.uid == uid)
        except StopIteration:
            return None


    def join(self, uid):
        user = self.find_user_in_room(uid)
        if user: return
        user = self.userdb.getUser(uid)
        if user: self.members.append(user)


    def leave(self, uid):
        user = self.find_user_in_room(uid)
        if user is None: return
        self.members.remove(user)
        self.reorder_djs()


    def dj(self, uid, plid=None):
        user = self.find_user_in_room(uid)
        if user is None: return

        index = max(user.dj for user in self.members if user and user.dj)

        if plid:
            user.playlist = plid
        else:
            user.playlist = self.playlist.getFirstPlaylistId(uid)

        if index is None:
            user.dj = 0
            self.current_dj = user
            self.next_song()
        else:
            user.dj = index + 1


    def undj(self, uid):
        user = self.find_user_in_room(uid)
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
        user = self.find_user_in_room(uid)
        if not user: return
        if plid:
            user.playlist = plid
        else: 
            user.playlist = self.playlist.getFirstPlaylistId(uid)


    def next_song(self):
        self.next_dj()
        dj = self.current_dj
        if not dj: 
            self.track = None
            self.track_start = None
            return
        if not dj.playlist:
            self.undj(dj.uid)
            self.next_song()
            return
        pl = self.playlist.loadPlaylist(dj.playlist, dj.uid)
        if not pl:
            self.undj(dj.uid)
            self.next_song()
            return
        self.track = pl[0]
        self.track_start = time.time()
        self.playlist.popPlaylist(dj.playlist)
