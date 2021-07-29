import time
from socket import  *
import json

class PositionClient():
    def __init__(self, config=None):
        print("POSCLIENT: Starting position client!")
        self.config = config
        self.host = "127.0.0.1"
        self.port = config['NETWORK']['position_port'] if config is not None else 13000
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.server_address = (self.host, self.port)
        self.connected=False

    def run_thread(self):
        print("POSCLIENT: Started Thread!")
        while not self.connected:
            try:
                self.socket = socket(AF_INET, SOCK_STREAM)
                self.socket.connect(self.server_address)
                self.connected = True
                print('POSCLIENT: Connecting to %s port %s' % self.server_address)
            except Exception as e:
                pass #Do nothing, just try again
            while self.connected:
                try: 
                    self.socket.recv(128)
                except:
                    print("POSCLIENT: Socket closed!")
                    self.connected = False
                    self.socket = None
                    break

    def send_pos(self, pos):
        try:
            if self.connected:
                print("POSCLIENT: Sending positions", flush=True)
                dump = json.dumps(pos).encode('utf-8')
                self.socket.sendall(dump)
        except:
            "POSCLIENT: Socket error!"