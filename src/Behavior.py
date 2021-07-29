import random
import time
import math
import threading
import numpy as np
import yaml #pyyaml
import queue
from pathlib import Path
import sys
from scipy.spatial import distance_matrix
from collections.abc import Iterable

from src.ui.debug_visualization import DebugVisualization
from src.net.position_client import PositionClient
from src.net.command_listener_server import CommandListenerServer
from src.net.joystick_server import JoystickServer
from src.net.dummy_joystick_client import DummyJoystickClient
from src.models.arena import Arena
from src.models.fish import Fish
from src.models.robot import Robot

# from PyQt5.sip import wrapinstance as wrapInstance

try:
    # new location for sip
    # https://www.riverbankcomputing.com/static/Docs/PyQt5/incompatibilities.html#pyqt-v5-11
    from PyQt5 import sip
except ImportError:
    import sip

from PyQt5.QtWidgets import QGraphicsEllipseItem, QLayout, QVBoxLayout, QHBoxLayout, QPushButton, QSpinBox, QLabel, QWidget, QApplication, QGraphicsView, QGraphicsScene, QCheckBox
from PyQt5.QtCore import (Qt, pyqtSignal, QObject, QEvent)
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
    update_ellipses = pyqtSignal(Robot, list, name="update_ellipses")
    
    def __init__(self, layout=None, DEBUG_VIS=None, config=None):
        super().__init__()

        # self.parent_layout = sip.wrapinstance(layout, QLayout)

        # load config
        self.config = config
        if config is None:
            path = Path(__file__).parent
            print(path)
            self.config = yaml.safe_load(open("cfg/config.yml"))

        self.debug_vis = DEBUG_VIS
        self.default_num_fish = self.config['DEFAULTS']['number_of_fish']

        #setup networking
        self.setup_networking()

        # setup ui
        parent_layout = layout if self.debug_vis is not None else self.setup_parameter_layout()
        self.setup_parameter_ui(parent_layout)

        #time step in seconds
        self.time_step = self.config['DEFAULTS']['time_step']

        # positions
        self.robot = None
        self.arena = Arena([0,0], self.config['ARENA']['width'], self.config['ARENA']['height'])

        self.zoa = self.config['DEFAULTS']['zoa']
        self.zoo = self.config['DEFAULTS']['zoo']
        self.zor = self.config['DEFAULTS']['zor']
        self.allfish = [Fish(id = i,  pos=np.asarray([random.randint(1, self.arena.width-1), random.randint(1, self.arena.height-1)]), ori=random.randint(0,360), arena=self.arena, config=self.config) for i in range(self.num_fish_spinbox.value())]

        # robot
        self.robot = Robot(self.arena, self.config)

        #step logger
        self._step_logger = []
        self.exec_time = 0
        self.exec_stepper = 0

        self.com_queue = queue.Queue()

        #setup debug vis
        if self.debug_vis is not None: self.setup_debug_vis()

        self.installEventFilter(self)

    def setup_parameter_layout(self):
        self.app = QApplication(sys.argv)
        layout = QVBoxLayout()

        title_label = QLabel('<h1>Parameter Window</h1>')
        layout.addWidget(title_label)
        title_label.move(60, 15)

        self.window = QWidget()
        self.window.setWindowTitle('Parameter window')
        self.window.setGeometry(100, 100, 200, 200)
        self.window.move(60, 15)
        self.window.setLayout(layout)
        self.window.show()
        
        return layout

    def setup_debug_vis(self):
        self.debug_vis.setArena(self.arena)

    def setup_networking(self):
        self.pos_client = PositionClient(self.config)
        self.command_server = CommandListenerServer(self, self.config)
        self.joystick_server = JoystickServer(self, self.config)

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

        if self.config["DEBUG"]["dummy_joystick_client"]:
            print("Behavior: running dummy joystick client")
            self.dummy_joystick_client = DummyJoystickClient(self.config)
            self.dj_thread = threading.Thread(target = self.dummy_joystick_client.run_thread)
            self.dj_thread.daemon = True
            self.dj_thread.start()

        self.update_positions.connect(self.pos_client.send_pos, Qt.QueuedConnection)

        # p_thread.join()
        # c_thread.join()
        # j_thread.join()

    def setup_parameter_ui(self, layout):
        self.parent_layout = layout
        self.layout = QVBoxLayout()

        random_target = QPushButton(f"Drive to new random point")
        random_target.clicked.connect(self.on_random_target_clicked, Qt.QueuedConnection)
        self.layout.addWidget(random_target)

        self.num_fish_layout = QHBoxLayout()
        num_fish_label = QLabel(f"Set number of fish:")
        self.num_fish_spinbox = QSpinBox()
        self.num_fish_spinbox.setRange(0,1000)
        self.num_fish_spinbox.setValue(self.default_num_fish)
        self.num_fish_layout.addWidget(num_fish_label)
        self.num_fish_layout.addWidget(self.num_fish_spinbox)
        self.layout.addLayout(self.num_fish_layout)

        self.reset_button = QPushButton(f"Reset fish")
        self.layout.addWidget(self.reset_button)

        # zone checkboxes
        self.zoa_checkbox = QCheckBox("Show zone of attraction")
        self.zoo_checkbox = QCheckBox("Show zone of orientation")
        self.zor_checkbox = QCheckBox("Show zone of repulsion")

        self.zoa_checkbox.setChecked(True)
        self.zoo_checkbox.setChecked(True)
        self.zor_checkbox.setChecked(True)

        self.layout.addWidget(self.zoa_checkbox)
        self.layout.addWidget(self.zoo_checkbox)
        self.layout.addWidget(self.zor_checkbox)

        #
        self.parent_layout.addLayout(self.layout)

        #connect 
        self.reset_button.clicked.connect(self.on_reset_button_clicked, Qt.QueuedConnection)
        self.num_fish_spinbox.valueChanged.connect(self.on_num_fish_spinbox_valueChanged, Qt.QueuedConnection)
        self.zoa_checkbox.stateChanged.connect(self.on_zone_checkbox_changed, Qt.QueuedConnection)
        self.zoo_checkbox.stateChanged.connect(self.on_zone_checkbox_changed, Qt.QueuedConnection)
        self.zor_checkbox.stateChanged.connect(self.on_zone_checkbox_changed, Qt.QueuedConnection)

    def on_random_target_clicked(self):
        self.target = random.randint(300, 900), random.randint(10, 90)
        if self.debug_vis is not None : self.debug_vis.scene.addEllipse(self.target[0], self.target[0], 10, 10)
        print(f"New target selected: {self.target[0]},{self.target[1]}")

    def on_reset_button_clicked(self):
        val = self.num_fish_spinbox.value()
        self.com_queue.put((self.reset_fish,val))
        print(f"Reseting positions of fish!")

    def on_zone_checkbox_changed(self):
        zones = [self.zor_checkbox.isChecked(), self.zoo_checkbox.isChecked(), self.zoa_checkbox.isChecked()]
        self.debug_vis.change_zones(zones)
        self.update_ellipses.emit(self.robot, self.allfish)

    def on_num_fish_spinbox_valueChanged(self, val):
        self.com_queue.put((self.reset_fish,val))
        print(f"Setting number of fish to: {val}")

    def eventFilter(self, obj, event):
        print("event!")
        if event.type() == QEvent.KeyPress and obj is self:
            print(event.key)

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

        # Move fish (simulate)
        # TODO: make fish react with robot
        # start_time = time.time()

        #execute all commands queue first
        while not(self.com_queue.empty()):
             command = self.com_queue.get()
            #  func = command[0]
             func = getattr(self, command[0])
             args = command[1:]
             func(*args)
        
        #update all fish one time step forward
        all_agents = [self.robot]
        all_agents.extend(self.allfish)
        all_pos = np.asarray([a.pos for a in all_agents])
        all_dir = np.asarray([a.dir for a in all_agents])
        dist_m = distance_matrix(all_pos, all_pos)

        for id_f, f in enumerate(all_agents):
            f.tick(all_pos, all_dir, dist_m[id_f])
        for f in all_agents:
            f.move()

        # Update fish in tracking view and send positions 
        self.update_positions.emit(self.serialize())

        # end_time = time.time()
        # exec_time = end_time-start_time
        # self.exec_stepper += 1
        # self.exec_time += exec_time
        # mean_exec_time  = self.exec_time / self.exec_stepper
        # print(f"mean tick takes {mean_exec_time} seconds; last tick took {exec_time} seconds")

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
            time.sleep(self.time_step)

    def __del__(self):
        # self.p_thread.
        # self.c_thread
        # self.j_thread
        pass

    def serialize(self):
        out=[]
        #robot
        out.append([np.rint(self.robot.pos).tolist(), np.around(self.robot.ori, decimals=2), self.robot.id])
        #fish 
        for a in self.allfish:
            out.append([np.rint(a.pos).tolist(), np.around(a.ori, decimals=2), a.id])

        return out

    def reset_fish(self, num):
        self.allfish = [Fish(id = i,  pos=np.asarray([random.randint(1, self.arena.width-1), random.randint(1, self.arena.height-1)]), ori=random.randint(0,360), arena=self.arena, config=self.config) for i in range(num)]
        self.update_ellipses.emit(self.robot, self.allfish)

    def queue_command(self, command):
        self.com_queue.put((command[0],command[1]))
        print("New command queued!")

    def control_robot(self, flag):
        self.robot.controlled = flag

    def change_robodir(self, dir):
        self.robot.new_dir = np.asarray(dir)

    def app_exec(self):
        sys.exit(self.app.exec_())
