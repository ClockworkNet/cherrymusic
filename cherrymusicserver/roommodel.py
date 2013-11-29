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
    UP   = 1
    DOWN = -1

    def __init__(self, path=None, started=None):
        self.upvotes = 0
        self.downvotes = 0
        self.voters = {} 
        self.started = started if started else time.time()
        if not path:
            self.path    = None
            self.abspath = None
            self.relpath = path
            self.info    = metainfo.MockTag()
        else:
            basedir = cherry.config['media.basedir']
            path = unquote(path)
            if path.startswith('/serve/'):
                path = path[7:]
            elif path.startswith('serve/'):
                path = path[6:]
            self.path = '/serve/' + path
            self.relpath = path
            self.abspath = os.path.join(basedir, path)
            self.info = metainfo.getSongInfo(self.abspath)
        self.load_info_properties()

    def upvote(self, member):
        if member.uid in self.voters:
            lastvote = self.voters[member.uid]
            if lastvote == self.UP: 
                return False
            else:
                self.downvotes -= 1
        self.voters[member.uid] = self.UP
        self.upvotes += 1
        return True

    def downvote(self, member):
        reversal = False
        if member.uid in self.voters:
            lastvote = self.voters[member.uid]
            if lastvote == self.DOWN: 
                return False
            else:
                reversal = True
                self.upvotes -= 1
        self.voters[member.uid] = self.DOWN
        self.downvotes += 1
        return reversal 

    @property
    def score(self):
        return self.upvotes - self.downvotes

    def load_info_properties(self):
        self.artist = self.info.artist
        self.album = self.info.album
        self.title = self.info.title
        self.track = self.info.track
        self.length = self.info.length

    def dict(self):
        d = self.info.dict()
        d['relpath'] = self.relpath
        d['path'] = self.path
        d['started'] = self.started
        d['upvotes'] = self.upvotes
        d['downvotes'] = self.downvotes
        d['score'] = self.score
        return d


class RoomMember():
    def __init__(self, user):
        self.uid = user.rowid
        self.name = user.username
        self.user = user
        self.dj = None
        self.points = user.points
        self.joined = time.time()
        self.playlist = None

    def dict(self, active=None):
        return {
            'uid': self.user.rowid,
            'name': self.user.username,
            'isadmin': self.user.isadmin,
            'realname': self.user.realname,
            'avatar_url': self.user.avatar_url,
            'public_url': self.user.public_url,
            'points': self.points,
            'playlist': self.playlist,
            'dj': self.dj,
            'joined': self.joined,
            'active': self.uid == active,
        }

class RoomChatter():
    def __init__(self):
        self.messages = [] 

    def say(self, member, message):
        log.i("Adding message from " + member.user.username + ": '" + message + "'")
        self.messages.append({
            'time': time.time(),
            'member': member,
            'message': message,
        })

    def dict(self, after=None):
        if after:
            messages = [m for m in self.messages if m.time > after]
        else:
            messages = self.messages
        def d(item):
            user = item.member.user
            return {
                    'time': item.time, 
                    'uid': user.uid,
                    'username': user.username,
                    'message': item.message,
                    }
        return [d(m) for m in messages]


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
        self.max_djs = cherry.config['room.max_djs']
        self.current_dj = None
        self.chatter = RoomChatter()


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
            next_index = 1

        try:
            self.current_dj = next(m for m in djs if m.dj == next_index)
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
            log.d("Member {0} was not found in room {1}".format(uid, self.name))
            return None


    def voting_member(self, uid):
        member = self.find_member(uid)
        if not member: return None
        if not self.current_dj: return None
        if self.current_dj.uid == uid: return None
        return member 


    def handle_command(member, cmd):
        if not member.admin: return False
        if cmd[0] != "\\": return False
        return False


    def say(self, uid, msg):
        member = self.find_member(uid)
        if not member or not msg: return
        if self.handle_command(member, msg): return
        self.chatter.say(member, msg)


    def upvote(self, uid):
        member = self.voting_member(uid)
        if not member: return
        if self.roomsong.upvote(member):
            self.current_dj.points += 1


    def downvote(self, uid):
        member = self.voting_member(uid)
        if not member: return
        if self.roomsong.downvote(member):
            self.current_dj.points -= 1


    def join(self, uid):
        member = self.find_member(uid)
        if member: return
        user = self.userdb.getUser(uid)
        if not user: return
        member = RoomMember(user)
        member.playlist = self.playlistdb.getFirstPlaylistId(uid)
        self.members.append(member)


    def leave(self, uid):
        member = self.find_member(uid)
        if member is None: return
        self.members.remove(member)
        self.reorder_djs()


    def dj(self, uid, plid=None):
        member = self.find_member(uid)
        if member is None: return
        if member.dj is not None: return

        if plid: member.playlist = plid

        index = max(m.dj for m in self.members)
        if index is None:
            member.dj = 1
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
        djs = self.get_djs()
        i = 1
        for m in djs:
            m.dj = i
            i += 1


    def select_playlist(self, uid, plid=None):
        member = self.find_member(uid)
        if not member: return
        if plid:
            member.playlist = int(plid)
        else: 
            member.playlist = self.playlistdb.getFirstPlaylistId(uid)
        log.i("selected {0} for member {1}".format(member.playlist, uid))

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


    def save_dj_points(self):
        dj = self.current_dj
        if not dj or dj.points == dj.user.points:
            return
        self.userdb.savePoints(dj.uid, dj.points)


    def next_song(self):
        self.save_dj_points()
        self.next_dj()
        dj = self.current_dj
        if not dj: 
            self.roomsong = RoomSong()
            log.d("No DJs; No songs")
            return
        if not dj.playlist:
            log.d("DJ {0} didn't have a playlist selected. Next.".format(dj.name))
            self.undj(dj.uid)
            self.next_song()
            return
        pl = self.playlistdb.loadPlaylist(dj.playlist, dj.uid, limit=1)
        if not pl:
            log.d("Couldn't find playlist {0} for DJ {1}. Next.".format(dj.playlist, dj.name))
            self.undj(dj.uid)
            self.next_song()
            return
        log.d("New song from playlist {0}: `{1}`".format(dj.playlist, pl[0].path))
        self.roomsong = RoomSong(pl[0].path)
        self.playlistdb.popPlaylist(dj.playlist)
