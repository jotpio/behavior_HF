import random
import time
import math
import threading

from src.ui.debug_visualization import DebugVisualization
from src.net.position_client import PositionClient
from src.net.command_listener_server import CommandListenerServer
from src.net.joystick_server import JoystickServer

# from PyQt5.sip import wrapinstance as wrapInstance

try:
    # new location for sip
    # https://www.riverbankcomputing.com/static/Docs/PyQt5/incompatibilities.html#pyqt-v5-11
    from PyQt5 import sip
except ImportError:
    import sip

from PyQt5.QtWidgets import QGraphicsEllipseItem, QLayout, QVBoxLayout, QHBoxLayout, QPushButton, QSpinBox, QLabel, QWidget, QApplication, QGraphicsView, QGraphicsScene
from PyQt5.QtCore import (Qt, pyqtSignal, QObject)
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter

# from robotracker import (
#     PythonBehavior,
#     RobotActionFlush,
#     RobotActionHalt,
#     RobotActionToTarget,
# )


# class Behavior(PythonBehavior):
class Behavior(QObject):
    update_positions = pyqtSignal(list, name="update_positions")
    update_ellipses = pyqtSignal(list, name="update_ellipses")
    
    def __init__(self, layout=None, DEBUG_VIS=None):
        super().__init__()  
        # self.parent_layout = sip.wrapinstance(layout, QLayout)

        self.debug_vis = DEBUG_VIS

        #setup networking
        self.setup_networking()

        # setup ui
        self.setup_parameter_ui(layout)

        # positions
        self.robot = None
        self.world = None
        self.fish = [[random.randint(300, 900), random.randint(300, 900), random.randint(0,360)] for i in range(self.num_fish_spinbox.value())]
        self.fish_max_speed = 10 #TODO: put this in config and GUI
        self.fish_max_turn = 5

        #step logger
        self._step_logger = []


    def setup_networking(self):
        self.pos_client = PositionClient()
        self.command_server = CommandListenerServer()
        self.joystick_server = JoystickServer()

        #setup threads
        print("Behavior: running position client")
        self.p_thread = threading.Thread(target = self.pos_client.run_thread)
        self.p_thread.daemon = True
        self.p_thread.start()

        print("Behavior: running command server")
        self.c_thread = threading.Thread(target = self.command_server.run_thread)
        self.c_thread.daemon = True
        self.c_thread.start()

        print("Behavior: running joystick server")
        self.j_thread = threading.Thread(target = self.joystick_server.run_thread)
        self.j_thread.daemon = True
        self.j_thread.start()

        self.update_positions.connect(self.pos_client.send_pos, Qt.QueuedConnection)


        # p_thread.join()
        # c_thread.join()
        # j_thread.join()

    def setup_parameter_ui(self, layout):
        # Example for custom GUI
        self.parent_layout = layout
        self.layout = QVBoxLayout()

        random_target = QPushButton(f"Drive to new random point")
        random_target.clicked.connect(self.on_random_target_clicked)
        self.layout.addWidget(random_target)

        self.num_fish_layout = QHBoxLayout()
        num_fish_label = QLabel(f"Set number of fish:")
        self.num_fish_spinbox = QSpinBox()
        self.num_fish_spinbox.setValue(4) #TODO: put this in config
        self.num_fish_layout.addWidget(num_fish_label)
        self.num_fish_layout.addWidget(self.num_fish_spinbox)
        self.layout.addLayout(self.num_fish_layout)

        self.parent_layout.addLayout(self.layout)

        #connect 
        self.num_fish_spinbox.valueChanged.connect(self.on_num_fish_spinbox_valueChanged)

    def on_random_target_clicked(self):
        self.target = random.randint(300, 900), random.randint(10, 90)
        self.debug_vis.scene.addEllipse(self.target[0], self.target[0], 10, 10)
        print(f"New target selected: {self.target[0]},{self.target[1]}")

    def on_num_fish_spinbox_valueChanged(self, val):
        self.fish = [[random.randint(300, 900), random.randint(300, 900), random.randint(0,360)] for i in range(val)]
        self.update_ellipses.emit(self.fish)
        print(f"Number of fish set to: {val}")

    def supported_timesteps(self):
        return []

    def activate(self, robot, world):
        self.robot = robot
        self.world = world

    def deactivate(self):
        self.robot = None
        self.world = None

    def next_speeds(self, robots, fish, timestep):
        # print("next_speeds")
        # log current positions to visualize in unity
        log_tuple = (timestep,) + tuple(robots) + tuple(self.fish)
        self._step_logger.append(log_tuple)

        # Move fish randomly (simulate)
        # TODO: make fish react with each other and robot
        # TODO: create fish behaviour model module
        
        for f in self.fish:
            old_rotation = f[2]
            oldPos = f[0], f[1]

            theta = math.radians(old_rotation)
            move_vector = (self.fish_max_speed * math.cos(theta)) + random.uniform(-self.fish_max_turn,self.fish_max_turn), (self.fish_max_speed * math.sin(theta)) + random.uniform(-self.fish_max_turn,self.fish_max_turn)
            new_rotation = math.degrees(math.atan2(move_vector[1], move_vector[0]))
            f[0] += move_vector[0] #TODO: change this to real speed not just distance addition
            f[1] += move_vector[1] #TODO: change this to real speed not just distance addition
            f[2] = new_rotation

        # Update fish in tracking view
        self.update_positions.emit(self.fish)
        # self.debug_vis.update_vis(self.fish)

        #region <to add when using with robotracker>
        # Move robots randomly
        # TODO: make robots interact with fish 
        # robots = [r for r in robots if r.uid == self.robot.uid]
        # if not robots:
        #     return [
        #         RobotActionFlush(self.robot.uid),
        #         RobotActionHalt(self.robot.uid, 0)
        #     ]
        # else:
        #     if self.target is not None:
        #         target = self.target
        #         self.target = None
        #         return [
        #             RobotActionFlush(self.robot.uid),
        #             RobotActionToTarget(
        #                 self.robot.uid, 0, (target[0], target[1])
        #             ),
        #         ]
        #     else:
        #         return []
        #endregion

    def run_thread(self):
        timestep = 0
        while True:
            self.next_speeds([],[], timestep)
            timestep += 1
            time.sleep(0.5)

    def __del__(self):
        # self.p_thread.
        # self.c_thread
        # self.j_thread
        pass




