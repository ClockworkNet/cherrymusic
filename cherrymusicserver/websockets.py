from ws4py.websocket import WebSocket

class RoomWebSocket(WebSocket):
    def opened(self):
        pass

    def closed(self, code, reason=None):
        pass

    def received_message(self, message):
        self.send(message.data, message.is_binary)
