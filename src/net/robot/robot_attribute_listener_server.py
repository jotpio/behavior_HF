from socket import *
import threading
import json
import sys
from PyQt5.QtCore import Qt, pyqtSignal, QObject
import time

from src.net.base.server import ServerListenerThread


class RobotAttributeListenerServer(ServerListenerThread):
    send_attributes = pyqtSignal(list, name="send_attributes")

    def __init__(self, parent, config=None):
        super().__init__(parent, "robot_attribute", config=config)
        self.send_attributes.connect(
            self.parent_behavior.queue_command, Qt.QueuedConnection
        )

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
                        amount_received += len(data)
                        # self.print(f"Received {data}")

                        self.send_attributes.emit(data)

                        # send received message
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

    def close_socket(self):
        # set real_robot to None
        self.send_attributes.emit(["set_next_attribute", "no robot"])

        return super().close_socket()
