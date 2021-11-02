from socket import *
from PyQt5.QtCore import Qt, pyqtSignal, QObject
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime

from src.net.server import ServerListenerThread


class JoystickServer(ServerListenerThread):
    send_robodir = pyqtSignal(list, name="send_robodir")
    control_robot = pyqtSignal(list, name="control_robot")

    def __init__(self, parent, config=None):
        super().__init__(parent, "joystick", config=config)

        self.send_robodir.connect(self.parent_behavior.queue_command)
        self.control_robot.connect(self.parent_behavior.queue_command)


        formatter = logging.Formatter("%(asctime)s -8s %(message)s")

        self.logger = logging.getLogger("input_logger")
        handler = TimedRotatingFileHandler(
            Path.home() / self.config["LOGGING"]["INPUT"], when="H", interval=1
        )
        handler.setFormatter(formatter)
        # handler.setLevel(logging.CRITICAL)
        self.logger.addHandler(handler)
        self.logcounter = 0

        self.logger.warning(f"Started a new joystick server: {datetime.now()}")

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

                        amount_received += len(data)
                        # print(f"JOYSERVER: Received {data}")

                        if data == "end connection":
                            self.print("Closing socket!")
                            self.close_socket()
                            break

                        if not self.debug:
                            parsed_data = self.parse_data(data)
                            self.control_robot.emit(["control_robot", True])
                            self.send_robodir.emit(["change_robodir", parsed_data])

                            # log direction every few ticks
                            if self.logcounter == 5:
                                self.logger.warning(f"{parsed_data}")
                                self.logcounter = 0
                            self.logcounter += 1
                except:
                    self.print("Socket error!")
                    self.close_socket()
                    break

    def close_socket(self):
        self.control_robot.emit(["control_robot", False])
        return super().close_socket()

    def parse_data(self, data):
        # data will have the shape "+/-x.xx, +/-x.xx", e.g. "+0.71, -0.13"
        try:
            split_data = data.split(", ")
            parsed_data = [
                float(split_data[0].replace(",", ".")),
                -float(split_data[1].replace(",", ".")),
            ]  # flip the y value
            return parsed_data
        except:
            self.print("Error in parsing joystick message!")
