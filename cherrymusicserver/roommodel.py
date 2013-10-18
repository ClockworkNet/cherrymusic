import cherrymusicserver as cherry

from cherrymusicserver import log
from cherrymusicserver import service
from cherrymusicserver import configuration

@service.user(cache='filecache')

class RoomModel:
    def __init__(self, name, message=None):
        self.name = name
        self.message = message

        self.track = None
        self.track_start = None

        self.users = []
        self.max_djs = cherry.config['room.max_djs']


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
        self.adjust_djs()


    def dj(self, userid):
        user = self.find_user(userid)
        if user is None: return
        user.dj = max(user.dj for user in self.users if user.dj is not None)


    def undj(self, userid):
        user = self.ind_user(userid)
        if user is None: return
        user.dj = None
        self.adjust_djs()


    """ Adjusts the order of the djs """
    def adjust_djs(self):

