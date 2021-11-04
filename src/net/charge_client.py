import time
from socket import *
import json
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from src.net.base.client import ClientSenderThread


class ChargeClient(ClientSenderThread):
    def __init__(self, parent, config=None):
        super().__init__(parent=parent, type="charge", config=config)
        self.command = None

    def run_thread(self):
        self.print("Started Thread!")
        while not self.connected:
            while self.command is not None:
                self.connect_socket()  # sets self.connected to True if successful

                # do stuff while connected
                if self.connected:
                    try:
                        dump = json.dumps(self.command).encode("utf-8")
                        self.socket.sendall(dump)
                    except:
                        self.print("Error while sending command!")
                        self.close_socket()
                        break

                    # wait for response
                    try:
                        response = self.socket.recv(8192).decode("utf-8")
                        if response == "received":
                            self.command = None
                        else:
                            self.print(f"Wrong response message: {response}")
                            self.close_socket()
                            break
                    except:
                        self.print("Error in getting response!")
                        self.close_socket()

            time.sleep(1)
            # while self.connected:
            #     try:
            #         data = self.socket.recv(8192).decode("utf-8")
            #         # print(f"data {data}")
            #         if data == "end connection":
            #             self.print("Connection closed")
            #             self.close_socket()
            #         if len(data) == 0:
            #             self.print("Empty data; closing socket!")
            #             self.close_socket()
            #             break
            #         if data == "received":
            #             continue
            #     except:
            #         self.print("Socket closed!")
            #         self.close_socket()
            #         break

    def send_command(self, command):
        self.command = command
        # try:
        #     if self.connected and self.socket:

        #         dump = json.dumps(command).encode("utf-8")
        #         self.socket.sendall(dump)
        # except:
        #     self.print("Socket error!")
        #     self.close_socket()
