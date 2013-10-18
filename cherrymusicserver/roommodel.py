import cherrymusicserver as cherry

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

        self.users = []
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
        djs = [user for user in self.users if user.dj is not None]
        return sorted(djs, key=lambda u: u.dj)


    def find_user_in_room(self, uid):
        if not self.users: return None
        try:
            return next(user for user in self.users if user and user.uid == uid)
        except StopIteration:
            return None


    def join(self, user):
        user = self.find_user_in_room(user.uid)
        if user: return
        self.users.append(user)


    def leave(self, uid):
        user = self.find_user_in_room(uid)
        if user is None: return
        self.users.remove(user)
        self.reorder_djs()


    def dj(self, uid):
        user = self.find_user_in_room(uid)
        if user is None: return

        index = max(user.dj for user in self.users if user and user.dj is not None)

        if index is None:
            user.dj = 0
            self.current_dj = user
            self.next_song()
        else:
            user.dj = index + 1


    def undj(self, uid):
        user = self.find_user_in_room(uid)
        if not user return
        user.dj = None
        self.reorder_djs()


    """ Adjusts the order of the djs """
    def reorder_djs(self):
        dj = 0
        def adjust(user):
            user.dj = dj
            dj += 1
        map(adjust, self.get_djs())


    def select_playlist(self, uid, plid):
        user = self.find_user_in_room(uid)
        if not user return
        self.load_user_playlists(user)


    def load_playlists(self, uid):
        user = self.find_user_in_room(uid)
        if not user return
        user.playlists = self.playlist.showPlaylists(uid)


    def next_song(self):
        self.next_dj()
        if not self.current_dj: 
            self.track = None
            self.track_start = None
            return
        if not self.current_dj.playlist:
            self.load_playlists(self.current_dj.uid)
        if not self.current_dj.playlist:
            playlist = self.current_dj.playlists[0]


