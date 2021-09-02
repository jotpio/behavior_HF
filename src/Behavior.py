from logging import debug
import random
import time
import math
import threading
import numpy as np
import yaml  # pyyaml
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
from src.ui.parameter_ui import Parameter_UI
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

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent

from PyQt5.QtGui import QPen, QBrush, QColor, QPainter

# from robotracker import (
#     PythonBehavior,
#     RobotActionFlush,
#     RobotActionHalt,
#     RobotActionToTarget,
# )

np.warnings.filterwarnings("error", category=np.VisibleDeprecationWarning)


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
        self.default_num_fish = self.config["DEFAULTS"]["number_of_fish"]
        self.optimisation = self.config["DEBUG"]["optimisation"]

        self.zoa = self.config["DEFAULTS"]["zoa"]
        self.zoo = self.config["DEFAULTS"]["zoo"]
        self.zor = self.config["DEFAULTS"]["zor"]

        # setup networking
        self.setup_networking()

        # setup ui
        parent_layout = (
            layout if self.debug_vis is not None else self.setup_parameter_layout()
        )
        self.setup_parameter_ui(parent_layout)

        # time step in seconds
        self.time_step = self.config["DEFAULTS"]["time_step"]
        self.skip_tick = False

        # positions
        self.robot = None
        self.arena = Arena(
            [0, 0], self.config["ARENA"]["width"], self.config["ARENA"]["height"]
        )

        self.allfish = [
            Fish(
                id=i + 1,
                pos=np.asarray(
                    [
                        random.randint(1, self.arena.width - 1),
                        random.randint(1, self.arena.height - 1),
                    ]
                ),
                ori=random.randint(0, 360),
                arena=self.arena,
                config=self.config,
            )
            for i in range(self.parameter_ui.num_fish_spinbox.value())
        ]

        # robot
        self.robot = Robot(self.arena, self.config)
        self.controlled = False

        # step logger
        self._step_logger = []
        self.exec_time = 0
        self.exec_stepper = 0

        self.com_queue = queue.LifoQueue()

        # setup debug vis
        if self.debug_vis is not None:
            self.setup_debug_vis()

        # catch key events
        if self.debug_vis is not None:
            app = QApplication.instance()
            app.installEventFilter(self)
        self.movelist = []

    def setup_parameter_layout(self):
        self.app = QApplication(sys.argv)
        layout = QVBoxLayout()

        title_label = QLabel("<h1>Parameter Window</h1>")
        layout.addWidget(title_label)
        title_label.move(60, 15)

        self.window = QWidget()
        self.window.setWindowTitle("Parameter window")
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

        # setup threads
        print("Behavior: running position client")
        self.p_thread = threading.Thread(target=self.pos_client.run_thread)
        self.p_thread.daemon = True
        self.p_thread.start()

        print("Behavior: running command server")
        self.c_thread = threading.Thread(target=self.command_server.run_thread)
        self.c_thread.daemon = True
        self.c_thread.start()

        print("Behavior: running joystick server")
        self.j_thread = threading.Thread(target=self.joystick_server.run_thread)
        self.j_thread.daemon = True
        self.j_thread.start()

        if self.config["DEBUG"]["dummy_joystick_client"]:
            print("Behavior: running dummy joystick client")
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

    def setup_parameter_ui(self, layout):
        self.parent_layout = layout

        self.parameter_ui = Parameter_UI(self)
        #
        self.parent_layout.addLayout(self.parameter_ui)

    def on_random_target_clicked(self):
        self.target = random.randint(300, 900), random.randint(10, 90)
        if self.debug_vis is not None:
            self.debug_vis.scene.addEllipse(self.target[0], self.target[0], 10, 10)
        print(f"New target selected: {self.target[0]},{self.target[1]}")

    def on_reset_button_clicked(self):
        val = self.parameter_ui.num_fish_spinbox.value()
        self.com_queue.put(("reset_fish", val))
        print(f"Reseting positions of fish!")

    def on_zone_checkbox_changed(self, bool):
        if self.debug_vis:
            zones = [
                self.parameter_ui.zor_checkbox.isChecked(),
                self.parameter_ui.zoo_checkbox.isChecked(),
                self.parameter_ui.zoa_checkbox.isChecked(),
            ]
            self.debug_vis.change_zones(zones)
            self.update_ellipses.emit(self.robot, self.allfish)

    def on_vision_checkbox_changed(self):
        if self.debug_vis:
            self.debug_vis.toggle_vision_cones(
                self.parameter_ui.vision_checkbox.isChecked()
            )
            self.update_ellipses.emit(self.robot, self.allfish)

    def on_num_fish_spinbox_valueChanged(self, val):
        self.com_queue.put(("reset_fish", val))
        print(f"Setting number of fish to: {val}")

    def on_zor_spinbox_valueChanged(self, val):
        zone_dir = {"zor": val}
        self.change_zones(zone_dir)

    def on_zoo_spinbox_valueChanged(self, val):
        zone_dir = {"zoo": val}
        self.change_zones(zone_dir)

    def on_zoa_spinbox_valueChanged(self, val):
        zone_dir = {"zoa": val}
        self.change_zones(zone_dir)

    def on_dark_mode_checkbox_changed(self):
        if self.debug_vis:
            self.debug_vis.toggle_dark_mode(
                self.parameter_ui.dark_mode_checkbox.isChecked()
            )
            self.update_ellipses.emit(self.robot, self.allfish)

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.KeyPress and obj is self.debug_vis.viz_window:
            key = event.key()
            # new_dir = np.asarray([0,0])
            if key == Qt.Key_W:
                self.robot.debug = True
                self.robot.controlled = True
                self.joystick_server.debug = True
                # new_dir += np.asarray([0,-1])
                self.movelist.append([0, -1])
                # print("W")
            if key == Qt.Key_A:
                self.robot.debug = True
                self.robot.controlled = True
                self.joystick_server.debug = True
                # new_dir += np.asarray([-1,0])
                self.movelist.append([-1, 0])
                # print("A")
            if key == Qt.Key_S:
                self.robot.debug = True
                self.robot.controlled = True
                self.joystick_server.debug = True
                # new_dir += np.asarray([0,1])
                self.movelist.append([0, 1])
                # print("S")
            if key == Qt.Key_D:
                self.robot.debug = True
                self.robot.controlled = True
                self.joystick_server.debug = True
                # new_dir += np.asarray([1,0])
                self.movelist.append([1, 0])
                # print("D")
            # new_dir = new_dir / np.linalg.norm(new_dir) if np.linalg.norm(new_dir) != 0 else np.asarray([0,0])
            # self.com_queue.put(("change_robodir", new_dir))
            # print(new_dir)
            return True
        elif event.type() == QEvent.KeyRelease and obj is self.debug_vis.viz_window:
            self.robot.debug = False
            self.robot.controlled = self.controlled
            self.joystick_server.debug = False
            return True

        elif event.type() == QEvent.Wheel and obj is self.debug_vis.viz_window:
            self.debug_vis.wheelEvent(event)

        return False

    def supported_timesteps(self):
        return []

    def activate(self, robot, world):
        self.robot = robot
        self.world = world

    def deactivate(self):
        self.robot = None
        self.world = None

    #
    # looping method
    #
    def next_speeds(self, robots, fish, timestep):
        # print("next_speeds")

        # Move fish (simulate)
        if self.optimisation:
            start_time = time.time()

        # execute all commands in queue first
        while not (self.com_queue.empty()):
            command = self.com_queue.get()
            if self.config["DEBUG"]["console"]:
                print(command)
            # last movement command is used (LIFO)
            if command[0] == "change_robodir":
                func = getattr(self, command[0])
                args = command[1:]
                func(*args)
                # print(command[1:])
            else:
                try:
                    func = getattr(self, command[0])
                    args = command[1:]
                    func(*args)
                except:
                    print(f"Command not found or error in command execution! {command}")

        # wasd robo movement
        if self.robot.debug and self.robot.controlled:
            robomove1 = np.unique(np.asarray(self.movelist), axis=0)
            robomove2 = np.sum(robomove1, axis=0)
            robomove3 = (
                robomove2 / np.linalg.norm(robomove2)
                if np.linalg.norm(robomove2) != 0
                else self.robot.dir
            )
            self.robot.new_dir = robomove3
            # print(robomove1, robomove2, robomove3)
        self.movelist = []

        # update all fish one time step forward (tick)
        all_agents = [self.robot]
        all_agents.extend(self.allfish)
        all_pos = np.asarray([np.array(a.pos, dtype=np.float64) for a in all_agents])
        all_dir = np.asarray([a.dir for a in all_agents])
        dist_m = distance_matrix(all_pos, all_pos)

        for id_f, f in enumerate(all_agents):
            if self.config["DEBUG"]["skip_ticks"]:
                if not self.skip_tick:
                    f.tick(all_pos, all_dir, dist_m[id_f])
            else:
                f.tick(all_pos, all_dir, dist_m[id_f])
                if id_f != 0:
                    robot_pos = all_pos[0]
                    robot_dir = all_dir[0]
                    f.check_following(robot_pos, robot_dir)
        if self.skip_tick:
            self.skip_tick = False
        else:
            self.skip_tick = True

        for f in all_agents:
            f.move()

        # Update fish in tracking view and send positions
        self.update_positions.emit(self.serialize())

        if self.optimisation:
            end_time = time.time()
            exec_time = end_time - start_time

            if self.exec_stepper == 100:
                self.exec_stepper = 0
                self.exec_time = 0
            self.exec_stepper += 1
            self.exec_time += exec_time
            mean_exec_time = self.exec_time / self.exec_stepper
            print(
                f"mean tick takes {mean_exec_time} seconds; last tick took {exec_time} seconds"
            )

        # region <to add when using with robotracker>
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
        # endregion

    def run_thread(self):
        timestep = 0
        while True:
            self.next_speeds([], [], timestep)
            timestep += 1
            time.sleep(self.time_step)

    def __del__(self):
        # self.p_thread.
        # self.c_thread
        # self.j_thread
        pass

    def app_exec(self):
        sys.exit(self.app.exec_())

    def serialize(self):
        out = []
        # robot
        # out.append([np.rint(self.robot.pos).tolist(), np.around(self.robot.ori, decimals=2), self.robot.id])
        robo_dict = {
            "id": self.robot.id,
            "orientation": np.around(self.robot.ori, decimals=2),
            "position": np.rint(self.robot.pos).tolist(),
        }
        out.append(robo_dict)
        # fish
        for a in self.allfish:
            fish_dict = {
                "id": a.id,
                "orientation": np.around(a.ori, decimals=2),
                "position": np.rint(a.pos).tolist(),
                "following": a.following,
                "repulsed": a.repulsed,
            }
            # out.append([np.rint(a.pos).tolist(), np.around(a.ori, decimals=2), a.id])
            out.append(fish_dict)

        return out

    def queue_command(self, command):
        self.com_queue.put((command[0], command[1]))
        print("New command queued!")

    #
    # Commands
    #

    def reset_fish(self, num):
        self.allfish = [
            Fish(
                id=i + 1,
                pos=np.asarray(
                    [
                        random.randint(1, self.arena.width - 1),
                        random.randint(1, self.arena.height - 1),
                    ]
                ),
                ori=random.randint(0, 360),
                arena=self.arena,
                config=self.config,
                dir=None,
                zor=self.zor,
                zoo=self.zoo,
                zoa=self.zoa,
            )
            for i in range(num)
        ]
        self.update_ellipses.emit(self.robot, self.allfish)

    def control_robot(self, flag):
        self.robot.controlled = flag
        self.controlled = flag

    def change_robodir(self, dir):
        np_dir = np.asarray(dir)
        dir_len = np.linalg.norm(np_dir)
        self.robot.new_dir = np_dir / dir_len if dir_len != 0 else np.asarray([0, 0])

    def change_zones(self, zone_dir):
        self.zor = zone_dir.get("zor", self.zor)
        self.zoo = zone_dir.get("zoo", self.zoo)
        self.zoa = zone_dir.get("zoa", self.zoa)

        self.robot.change_zones(self.zor, self.zoo, self.zoa)
        for f in self.allfish:
            f.change_zones(self.zor, self.zoo, self.zoa)

        if self.debug_vis:
            self.update_ellipses.emit(self.robot, self.allfish)

        self.parameter_ui.zor_spinbox.setValue(self.zor)
        self.parameter_ui.zoo_spinbox.setValue(self.zoo)
        self.parameter_ui.zoa_spinbox.setValue(self.zoa)

    def set_zone_preset(self, size):
        if size == 0:
            self.zor = self.config["ZONE_MODES"]["SMALL"]["zor"]
            self.zoo = self.config["ZONE_MODES"]["SMALL"]["zoo"]
            self.zoa = self.config["ZONE_MODES"]["SMALL"]["zoa"]

        if size == 1:
            self.zor = self.config["ZONE_MODES"]["LARGE"]["zor"]
            self.zoo = self.config["ZONE_MODES"]["LARGE"]["zoo"]
            self.zoa = self.config["ZONE_MODES"]["LARGE"]["zoa"]

        for f in self.allfish:
            f.change_zones(self.zor, self.zoo, self.zoa)

        if self.debug_vis:
            self.update_ellipses.emit(self.robot, self.allfish)

        self.parameter_ui.zor_spinbox.setValue(self.zor)
        self.parameter_ui.zoo_spinbox.setValue(self.zoo)
        self.parameter_ui.zoa_spinbox.setValue(self.zoa)

