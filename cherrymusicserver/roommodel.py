import cherrymusicserver as cherry

from cherrymusicserver import log
from cherrymusicserver import service
from cherrymusicserver import configuration

@service.user(cache='filecache', model='cherrymodel', playlistdb='playlist', userdb='users')
class RoomModel:
    def __init__(self, name, message=None):
        self.name = name
        self.message = message

        self.track = None
        self.track_start = None

        self.users = []
        self.max_djs = cherry.config['room.max_djs']
        self.current_dj = None


    def next_dj(self):
        djs = self.get_djs()

        if not djs: 
            self.current_dj = None
            return

        if self.current_dj:
            index = self.current_dj.dj + 1 % self.max_djs
        else:
            index = 0

        self.current_dj = next(user for user in djs if djs.dj == index)
        return self.current_dj


    def get_djs(self):
        djs = [user for user in self.users if user.dj is not None]
        return sorted(djs, key=lambda u: u.dj)


    def find_user(self, userid):
        return next(user for user in self.users if user.userid == userid)


    def join(self, user):
        user = self.find_user(userid)
        if user: return
        self.users.append(user)


    def leave(self, userid):
        user = self.find_user(userid)
        if user is None: return
        self.users.remove(user)
        self.reorder_djs()


    def dj(self, userid):
        user = self.find_user(userid)
        if user is None: return

        index = max(user.dj for user in self.users if user.dj is not None)

        if index is None:
            user.dj = 0
            self.current_dj = user
            self.start_playing()
        else:
            user.dj = index + 1


    def undj(self, userid):
        user = self.ind_user(userid)
        if user is None: return
        user.dj = None
        self.reorder_djs()


    """ Adjusts the order of the djs """
    def reorder_djs(self):
        def adjust(user):
            user.dj = dj++
        map(adjust, self.get_djs())


    """ @todo
    def start_playing(self):
        if not self.current_dj: 
            return False
        if self.current_dj.playlist:
            self.track = ?
        elif: self.current_dj.playlists:
            self.current_dj.playlist = self.current_dj.playlists[0]
            self.track = ?
        else:
            return False
    """
