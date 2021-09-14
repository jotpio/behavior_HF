from socket import *
from PyQt5.QtCore import Qt, pyqtSignal, QObject

from src.net.server import ServerListenerThread


class JoystickServer(ServerListenerThread):
    send_robodir = pyqtSignal(list, name="send_robodir")
    control_robot = pyqtSignal(list, name="control_robot")

    def __init__(self, parent, config=None):
        super().__init__(parent,"joystick", config=config)

        self.send_robodir.connect(
            self.parent_behavior.queue_command
        )
        self.control_robot.connect(
            self.parent_behavior.queue_command
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

                        amount_received += len(data)
                        # print(f"JOYSERVER: Received {data}")

                        if data == "end control":
                            self.control_robot.emit(["control_robot",False])

                        if not self.debug:
                            parsed_data = self.parse_data(data)
                            self.control_robot.emit(["control_robot",True])
                            self.send_robodir.emit(['change_robodir', parsed_data])
                except:
                    self.print("Socket error!")
                    self.close_socket()
                    break

    def close_socket(self):
        self.control_robot.emit(["control_robot",False])
        return super().close_socket()

    def parse_data(self, data):
        # data will have the shape "+/-x.xx, +/-x.xx", e.g. "+0.71, -0.13"
        split_data = data.split(", ")
        parsed_data = [float(split_data[0]), -float(split_data[1])] # flip the y value
        return parsed_data
