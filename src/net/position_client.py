import time
from socket import *
import json
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from src.net.client import ServerListenerThread



class PositionClient(ServerListenerThread):
    def __init__(self, parent, config=None):
        super().__init__(parent=parent, type="position", config=config)

    def send_pos(self, pos):
        try:
            # print("POSCLIENT: Trying to send positions", flush=True)
            if self.connected and self.socket:
                # print("POSCLIENT: Sending positions", flush=True)
                dump = json.dumps(pos).encode("utf-8")
                self.socket.sendall(dump)
        except:
            print("POSCLIENT: Socket error!")
            self.close_socket()