import time
from socket import *
import json
from PyQt5.QtCore import Qt, pyqtSignal, QObject
import logging

FORMAT = "\t%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


class ClientSenderThread(QObject):
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
        self.debug = self.config["DEBUG"]["console"]
        self.parent_behavior = parent

    def run_thread(self):
        self.print("Started Thread!")
        while not self.connected:

            self.connect_socket()  # sets self.connected to True if successful

            # do stuff while connected
            if self.connected:
                self.print("Testing connection...")
            while self.connected:
                try:
                    data = self.socket.recv(8192).decode("utf-8")
                    # print(f"data {data}")
                    if data == "end connection":
                        self.print("Connection closed")
                        self.close_socket()
                    if len(data) == 0:
                        self.print("Empty data; closing socket!")
                        self.close_socket()
                        break
                    if data == "received":
                        continue
                except:
                    self.print("Socket closed!")
                    self.close_socket()
                    break

    def print(self, message):
        logging.info(f"\t{self.type.upper()}: {message}")

    def connect_socket(self):
        try:
            if self.debug:
                self.print("Trying to connect...")
            if not self.connected and self.socket is None:
                self.socket = socket(AF_INET, SOCK_STREAM)
                self.socket.connect(self.server_address)
                self.connected = True

                self.print("Connecting to %s port %s" % self.server_address)
            else:
                raise Exception(f"{self.type.upper()}: Could not connect socket!")
        except Exception as e:
            if self.debug:
                self.print("Error while attempting to connect!")
            time.sleep(1)  # Do nothing, just try again
            self.close_socket()

    def close_socket(self):
        if self.socket:
            self.socket.close()
        self.socket = None
        self.connected = False
