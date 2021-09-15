import time
from socket import *
import json
from PyQt5.QtCore import Qt, pyqtSignal, QObject



class ServerListenerThread(QObject):
    def __init__(self, parent, type, config=None):
        super().__init__()

        self.type = type
        self.print(f"Starting {self.type} client!")
        self.config = config
        self.host = "127.0.0.1"
        self.port = config["NETWORK"][f"{type}_port"]
        self.socket = None
        self.server_address = (self.host, self.port)
        self.connected = False
        self.debug = False
        self.parent_behavior = parent


    def run_thread(self):
        self.print("Started Thread!")
        while not self.connected:
            
            self.connect_socket() #sets self.connected to True if successful
            
            #do stuff while connected
            while self.connected:
                try:
                    self.print("Testing connection...")
                    data = self.socket.recv(8192).decode("utf-8")
                    # print(f"data {data}")
                    if data == "end connection":
                        self.print("Connection closed")
                        self.close_socket()
                except:
                    self.print("Socket closed!")
                    self.close_socket()
                    break

    def print(self, message):
        print(f"{self.type.upper()}: {message}", flush=True)

    def connect_socket(self):
        try:
            print("POSCLIENT: Trying to connect...")
            if not self.connected and self.socket is None:
                self.socket = socket(AF_INET, SOCK_STREAM)
                self.socket.connect(self.server_address)
                self.connected = True

                print("Connecting to %s port %s" % self.server_address)
            else:
                raise Exception(f"{self.type.upper()}: Could not connect socket!")
        except Exception as e:
            time.sleep(1)  # Do nothing, just try again
            self.close_socket()

    def close_socket(self):
        self.socket.close()
        self.socket = None
        self.connected = False
