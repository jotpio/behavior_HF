import threading
from PyQt5.QtCore import Qt, pyqtSignal, QObject

from src.net.position_client import PositionClient
from src.net.command_listener_server import CommandListenerServer
from src.net.joystick_server import JoystickServer
from src.net.charge_client import ChargeClient

from src.models.robot import Robot


class NetworkController(QObject):

    update_positions = pyqtSignal(list, name="update_positions")
    update_ellipses = pyqtSignal(Robot, list, name="update_ellipses")
    charge_command = pyqtSignal(dict, name="update_ellipses")

    def __init__(self, parent, config):
        super().__init__()
        self.behavior = parent
        self.config = config

    def setup_networking(self):
        self.pos_client = PositionClient(self.behavior, self.config)
        self.command_server = CommandListenerServer(self.behavior, self.config)
        self.joystick_server = JoystickServer(self.behavior, self.config)
        self.charge_client = ChargeClient(self.behavior, self.config)

        # setup threads
        self.p_thread = threading.Thread(target=self.pos_client.run_thread)
        self.p_thread.daemon = True
        self.p_thread.start()

        self.c_thread = threading.Thread(target=self.command_server.run_thread)
        self.c_thread.daemon = True
        self.c_thread.start()

        self.j_thread = threading.Thread(target=self.joystick_server.run_thread)
        self.j_thread.daemon = True
        self.j_thread.start()

        self.ch_thread = threading.Thread(target=self.charge_client.run_thread)
        self.ch_thread.daemon = True
        self.ch_thread.start()

        self.update_positions.connect(self.pos_client.send_pos, Qt.QueuedConnection)
        self.charge_command.connect(
            self.charge_client.send_command, Qt.QueuedConnection
        )

    def exit(self):
        self.p_thread.join()
        self.c_thread.join()
        self.j_thread.join()
        self.ch_thread.join()
