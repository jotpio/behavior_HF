from socket import *
import json
import time
from PyQt5.QtCore import Qt, pyqtSignal, QObject


class ServerListenerThread(QObject):
    def __init__(self, parent, type, config=None):
        super().__init__()
        self.type = type
        self.print(f"Starting {type} server!")
        self.config = config
        self.host = "127.0.0.1"
        self.port = config["NETWORK"][f"{type}_port"]
        self.socket = None
        self.parent_behavior = parent
        
        self.debug = False
        self.connected = False

    def run_thread(self):
        while True:
            successful = self.start_server()
            # retry server start if not successful
            if not successful:
                continue

            # do things while connected
            while self.connected:
                try:
                    amount_received = 0
                    while amount_received < 4096:
                        data = self.conn.recv(4096).decode("utf-8")
                        
                        if len(data) == 0:
                            self.print("Empty data; closing socket!")
                            self.close_socket()
                            break

                        try:
                            data = json.loads(data)
                        except:
                            self.print("Error decoding message!")
                        amount_received += len(data)
                        # print(f"JOYSERVER: Received {data}")
                except:
                    self.print("Socket error!")
                    self.close_socket()
                    break

    def initiate_socket(self):
        if not self.connected and self.socket is None:
            self.socket = socket(AF_INET, SOCK_STREAM)
            self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
        else:
            raise Exception(f"{self.type.upper()}: Could not initiate socket!") 

    def close_socket(self):
        if self.socket:
            if self.connected:
                self.socket.shutdown(1)
        self.socket.close()
        self.socket = None
        self.connected = False

    def start_server(self):
        try:
            # Initiate socket
            self.initiate_socket()
        except:
            self.print(f"{self.port} already in use!")
            self.close_socket()
            time.sleep(0.3) # wait a little before retrying socket bind
            return False

        try:
            self.socket.listen()  # enable server to accept connections
            self.print("Waiting for connection...")
            self.conn, address = self.socket.accept()  # wait for connection
            self.print(f"Server connected by {address}")
            self.connected = True

        except:
            self.print(f"{self.port} error while connecting to client!")
            self.close_socket()
            time.sleep(0.3) # wait a little before retrying socket listen
            return False

        return True

    def print(self, message):
        print(f"{self.type.upper()}: {message}", flush=True)


    # Deleting (Calling destructor)
    def __del__(self):
        if self.socket and self.connected:
            self.socket.shutdown(
                SHUT_RDWR
            )  # SHUT_RDWR: further sends and receives are disallowed
            self.socket.close()
            self.socket = None
        self.print("Destructor called, Server deleted.")