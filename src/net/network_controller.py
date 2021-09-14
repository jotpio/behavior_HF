import threading
from PyQt5.QtCore import Qt, pyqtSignal, QObject

from src.net.position_client import PositionClient
from src.net.command_listener_server import CommandListenerServer
from src.net.joystick_server import JoystickServer
from src.net.dummy_joystick_client import DummyJoystickClient
from src.models.robot import Robot


class NetworkController(QObject):

    update_positions = pyqtSignal(list, name="update_positions")
    update_ellipses = pyqtSignal(Robot, list, name="update_ellipses")

    def __init__(self, parent, config):
        super().__init__()
        self.behavior = parent
        self.config = config

    def setup_networking(self):
        self.pos_client = PositionClient(self.behavior, self.config)
        self.command_server = CommandListenerServer(self.behavior, self.config)
        self.joystick_server = JoystickServer(self.behavior, self.config)

        # setup threads
        print("Network: running position client")
        self.p_thread = threading.Thread(target=self.pos_client.run_thread)
        self.p_thread.daemon = True
        self.p_thread.start()

        print("Network: running command server")
        self.c_thread = threading.Thread(target=self.command_server.run_thread)
        self.c_thread.daemon = True
        self.c_thread.start()

        print("Network: running joystick server")
        self.j_thread = threading.Thread(target=self.joystick_server.run_thread)
        self.j_thread.daemon = True
        self.j_thread.start()

        if self.config["DEBUG"]["dummy_joystick_client"]:
            print("Network: running dummy joystick client")
            self.dummy_joystick_client = DummyJoystickClient(self.config)
            self.dj_thread = threading.Thread(
                target=self.dummy_joystick_client.run_thread
            )
            self.dj_thread.daemon = True
            self.dj_thread.start()

        self.update_positions.connect(self.pos_client.send_pos, Qt.QueuedConnection)

        # p_thread.join()
        # c_thread.join()
        # j_thread.join()
            
    def exit(self):    
        self.p_thread.join()
        self.c_thread.join()
        self.j_thread.join()
