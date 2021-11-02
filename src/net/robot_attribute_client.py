import time
from socket import *
import json
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from src.net.client import ClientSenderThread

import sys
import yaml
import threading

from PyQt5.QtWidgets import QLayout, QVBoxLayout, QPushButton
from PyQt5.sip import wrapinstance as wrapInstance

from pathlib import Path

path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))


class RobotAttributeClient(ClientSenderThread):
    def __init__(self, parent, config=None):
        super().__init__(parent=parent, type="robot_attribute", config=config)

    def send_robot_attributes(self, robot):
        self.current_robot = robot

    def run_thread(self):
        self.print("Started Thread!")
        while not self.connected:
            self.connect_socket()  # sets self.connected to True if successful
            while self.current_robot is not None:
                # do stuff while connected
                if self.connected:
                    try:
                        dump = json.dumps(self.current_robot).encode("utf-8")
                        self.socket.sendall(dump)
                    except:
                        self.print("Error while sending command!")
                        self.close_socket()
                        break

                    # wait for response
                    try:
                        response = self.socket.recv(8192).decode("utf-8")
                        if response == "received":
                            continue
                        else:
                            self.print(f"Wrong response message: {response}")
                            self.close_socket()
                            break
                    except:
                        self.print("Error in getting response!")
                        self.close_socket()

                time.sleep(1)


if __name__ == "__main__":

    try:

        path = (Path(__file__).parents[1]) / "../cfg/config.yml"
        print(f"BEHAVIOR: config path: {path}")
        config = yaml.safe_load(open(path))
        s = RobotAttributeClient(None, config=config)
        thread = threading.Thread(target=s.run_thread)
        thread.daemon = True
        thread.start()
        # thread.join()
        while thread.is_alive():
            thread.join(1)  # not sure if there is an appreciable cost to this.

    except (KeyboardInterrupt, SystemExit):
        print("\n! Received keyboard interrupt, quitting threads.\n")
        s.socket.close()
        sys.exit()
