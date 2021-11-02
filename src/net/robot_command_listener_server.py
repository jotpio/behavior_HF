from socket import *
import threading
import json
import sys
from PyQt5.QtCore import Qt, pyqtSignal, QObject
import time

from src.net.server import ServerListenerThread


class RobotCommandListenerServer(ServerListenerThread):
    # send_command = pyqtSignal(list, name="send_command")

    def __init__(self, parent, config=None):
        super().__init__(parent, "robot_command", config=config)
        # self.send_command.connect(
        #     self.parent_behavior.set_next_command, Qt.QueuedConnection
        # )

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

                        if data == "end connection":
                            self.print("closing socket!")
                            self.close_socket()
                            break

                        try:
                            data = json.loads(data)
                        except:
                            self.print(f"Error decoding message: {data}")
                            break
                        amount_received += len(data)
                        self.print(f"Received {data}")

                        self.parent_behavior.set_next_command(data)

                        # send received message to unity
                        try:

                            message = "received"
                            self.conn.sendall(message.encode("utf-8"))
                        except:
                            self.print(f"Error sending 'received' message!")
                            break

                except:
                    self.print("Socket error!")
                    self.close_socket()
                    break
