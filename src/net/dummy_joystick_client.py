import time
from socket import *
import json
from PyQt5.QtCore import Qt, pyqtSignal, QObject
import numpy as np


class ClientSenderThread(QObject):
    def __init__(self):
        super().__init__()

        self.type = "dummy_joy"
        self.print(f"Starting {self.type} client!")
        self.host = "127.0.0.1"
        self.port_com = 13001
        self.port_joy = 13002
        self.socket = None
        self.server_address_com = (self.host, self.port_com)
        self.server_address_joy = (self.host, self.port_joy)
        self.connected = False
        self.debug = True
        self.two_pi_range = np.linspace(0, 2 * np.pi, 100)
        self.current_dir_id = 0

        self.done = False

    def run_thread(self):
        self.print("Started Thread!")

        # send joystick directiosns
        while not self.connected:

            self.connect_socket_joy()  # sets self.connected to True if successful

            # do stuff while connected
            if self.connected:
                self.print("Sending joystick data...")
            while self.connected:
                try:
                    current_angle = self.two_pi_range[self.current_dir_id]
                    current_dir = np.cos(current_angle) * np.asarray([1, 0]) + np.sin(
                        current_angle
                    ) * np.asarray([0, 1])

                    x_sign = "+" if np.sign(current_dir[0]) == 1 else ""
                    y_sign = "+" if np.sign(current_dir[1]) == 1 else ""
                    out_dir = f"{x_sign}{current_dir[0]}, {y_sign}{current_dir[1]}"

                    self.print(out_dir)
                    self.socket.sendall(out_dir.encode("utf-8"))

                    self.current_dir_id += 1

                    if self.current_dir_id == 100:
                        self.current_dir_id = 0

                    time.sleep(0.1)
                    # if done wait for response and close socket
                    if self.done:
                        data = self.socket.recv(8192)
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
        print(f"\t{self.type.upper()}: {message}", flush=True)

    def connect_socket_com(self):
        try:
            if self.debug:
                self.print("Trying to connect...")
            if not self.connected and self.socket is None:
                self.socket = socket(AF_INET, SOCK_STREAM)
                self.socket.connect(self.server_address_com)
                self.connected = True

                self.print("Connecting to %s port %s" % self.server_address_com)
            else:
                raise Exception(f"{self.type.upper()}: Could not connect socket!")
        except Exception as e:
            if self.debug:
                self.print("Error while attempting to connect!")
            time.sleep(1)  # Do nothing, just try again
            self.close_socket()

    def connect_socket_joy(self):
        try:
            if self.debug:
                self.print("Trying to connect...")
            if not self.connected and self.socket is None:
                self.socket = socket(AF_INET, SOCK_STREAM)
                self.socket.connect(self.server_address_joy)
                self.connected = True

                self.print("Connecting to %s port %s" % self.server_address_joy)
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


if __name__ == "__main__":
    dummy = ClientSenderThread()
    dummy.run_thread()

