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


path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))
# print(sys.path)

from src.net.network_controller import NetworkController
from src.ui.parameter_ui import Parameter_UI
from src.models.arena import Arena
from src.models.fish import Fish
from src.models.robot import Robot
from src.models.agent import (
    attract,
    repulse,
    align,
    check_in_radii_vision,
    normalize,
    get_zone_neighbours,
)
from src.util.util import Util

from PyQt5.sip import wrapinstance as wrapInstance

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent

# from PyQt5.QtWidgets import QLayout, QVBoxLayout, QPushButton

# from PyQt5.QtGui import QPen, QBrush, QColor, QPainter

try:
    from robotracker import (
        PythonBehavior,
        RobotActionFlush,
        RobotActionHalt,
        RobotActionToTarget,
    )

    RT_MODE = True
except:
    print("No RoboTracker found!")
    RT_MODE = False

np.warnings.filterwarnings("error", category=np.VisibleDeprecationWarning)


# class Behavior(PythonBehavior):
class Behavior(QObject):
    def __init__(self, layout=None, DEBUG_VIS=None, config=None):
        super().__init__()

        self.robot = None
        self.world = None
        self.target = None

        # load config
        self.config = config
        if self.config is None:
            path = (Path(__file__).parents[1]) / "cfg/config.yml"
            print(f"Behavior: config path: {path}")
            self.config = yaml.safe_load(open(path))

        self.util = Util(self.config)
        self.debug_vis = DEBUG_VIS
        # if DEBUG_VIS is None:
        #     self.debug_vis = DebugVisualization(self.config, RT_MODE)

        self.default_num_fish = self.config["DEFAULTS"]["number_of_fish"]
        self.optimisation = self.config["DEBUG"]["optimisation"]

        self.zoa = self.config["DEFAULTS"]["zoa"]
        self.zoo = self.config["DEFAULTS"]["zoo"]
        self.zor = self.config["DEFAULTS"]["zor"]

        # setup networking
        self.network_controller = NetworkController(self, self.config)
        self.network_controller.setup_networking()

        # time step in seconds
        self.time_step = self.config["DEFAULTS"]["time_step"]

        # arena
        self.arena = Arena(
            [0, 0], self.config["ARENA"]["width"], self.config["ARENA"]["height"]
        )

        # initialize robot
        self.behavior_robot = Robot(self.arena, self.config)
        # self.controlled = False
        self.trigger_next_robot_step = False
        self.flush_robot_target = False

        # # initialize fish
        self.reset_fish(self.config["DEFAULTS"]["number_of_fish"])

        self.initiate_numba()

        # setup ui
        if RT_MODE:
            try:
                self.parent_layout = wrapInstance(layout, QLayout)
            except:
                print(f"Behavior: Error with layout wrapping. Creating own one...")
                self.parent_layout = (
                    layout
                    if self.debug_vis is not None
                    else self.setup_parameter_layout()
                )
        else:
            self.parent_layout = (
                layout if self.debug_vis is not None else self.setup_parameter_layout()
            )

        self.setup_parameter_ui()  # fill parameter layout

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

        print("Behavior: Initialized!")

    def initiate_numba(self):
        repulse(np.asarray([[0.0, 0.0]]), np.asarray([0, 0]))
        align(np.asarray([[0.0, 0.0]]))
        attract(np.asarray([[0.0, 0.0]]), np.asarray([0, 0]))
        check_in_radii_vision(
            np.asarray([[0.0, 0.0]]),
            np.asarray([[0.0, 0.0]]),
            np.asarray([[0.0, 0.0]]),
            0.0,
            np.asarray([0.0, 0.0]),
            np.asarray([0.0, 0.0]),
        )
        get_zone_neighbours(
            np.asarray([1.4, 2.0, 43.0321, 4214.3123]),
            np.zeros((5, 2)),
            np.zeros((5, 2)),
            10,
            50,
            150,
        )
        normalize(np.asarray([1.4, 2.0]))

    def setup_parameter_layout(self):
        print("Behavior: Setting up parameter layout")
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

    def setup_parameter_ui(self):
        print("Behavior: Setting up parameter ui")
        self.parameter_ui = Parameter_UI(self, RT_MODE, self.config)
        #
        self.parent_layout.addLayout(self.parameter_ui)

    def on_random_target_clicked(self):
        self.target = random.randint(10, 45), random.randint(10, 45)
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
            self.network_controller.update_ellipses.emit(
                self.behavior_robot, self.allfish
            )

    def on_vision_checkbox_changed(self):
        if self.debug_vis:
            self.debug_vis.toggle_vision_cones(
                self.parameter_ui.vision_checkbox.isChecked()
            )
            self.network_controller.update_ellipses.emit(
                self.behavior_robot, self.allfish
            )

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
            self.network_controller.update_ellipses.emit(
                self.behavior_robot, self.allfish
            )

    # robot slots
    def on_auto_robot_checkbox_changed(self, val):
        self.behavior_robot.controlled = not val
        self.parameter_ui.next_robot_step.setEnabled(not val)
        self.parameter_ui.flush_robot_button.setEnabled(not val)

    # if auto robot movement is disabled then the next automatic robot movement target can be triggered by this button or manually by the joystick movement
    def on_next_robot_step_clicked(self):
        self.trigger_next_robot_step = True

    def on_flush_robot_target_clicked(self):
        self.flush_robot_target = True

    def on_sel_target_pb_clicked(self):
        target_x = self.util.map_px_to_cm(self.parameter_ui.target_x.value())
        target_y = self.util.map_px_to_cm(self.parameter_ui.target_y.value())
        self.target = target_x, target_y
        if self.debug_vis is not None:
            self.debug_vis.scene.addEllipse(
                self.util.map_cm_to_px(self.target[0]),
                self.util.map_cm_to_px(self.target[1]),
                10,
                10,
            )
        print(f"New target selected: {self.target[0]},{self.target[1]}")

    def on_turn_right_pb_clicked(self):
        self.turn_right = True

    def on_turn_left_pb_clicked(self):
        self.turn_left = True

    def on_turn_left_pb_released(self):
        self.turn_left = False

    def on_turn_right_pb_released(self):
        self.turn_right = False

    def on_sim_charge_pb_clicked(self):
        self.go_to_charging_station = True

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.KeyPress and obj is self.debug_vis.viz_window:
            key = event.key()
            # new_dir = np.asarray([0,0])
            if key == Qt.Key_W:
                self.behavior_robot.debug = True
                self.behavior_robot.controlled = True
                self.network_controller.joystick_server.debug = True
                # new_dir += np.asarray([0,-1])
                self.movelist.append([0, -1])
                # print("W")
            if key == Qt.Key_A:
                self.behavior_robot.debug = True
                self.behavior_robot.controlled = True
                self.network_controller.joystick_server.debug = True
                # new_dir += np.asarray([-1,0])
                self.movelist.append([-1, 0])
                # print("A")
            if key == Qt.Key_S:
                self.behavior_robot.debug = True
                self.behavior_robot.controlled = True
                self.network_controller.joystick_server.debug = True
                # new_dir += np.asarray([0,1])
                self.movelist.append([0, 1])
                # print("S")
            if key == Qt.Key_D:
                self.behavior_robot.debug = True
                self.behavior_robot.controlled = True
                self.network_controller.joystick_server.debug = True
                # new_dir += np.asarray([1,0])
                self.movelist.append([1, 0])
                # print("D")
            # new_dir = new_dir / np.linalg.norm(new_dir) if np.linalg.norm(new_dir) != 0 else np.asarray([0,0])
            # self.com_queue.put(("change_robodir", new_dir))
            # print(new_dir)
            return True
        elif event.type() == QEvent.KeyRelease and obj is self.debug_vis.viz_window:
            self.behavior_robot.debug = False
            self.behavior_robot.controlled = self.controlled
            self.network_controller.joystick_server.debug = False
            return True

        elif event.type() == QEvent.Wheel and obj is self.debug_vis.viz_window:
            self.debug_vis.wheelEvent(event)

        return False

    def supported_timesteps(self):
        print("Behavior: supported_timesteps called")
        return []

    def activate(self, robot, world):
        print("Behavior: Activated")
        self.robot = robot
        self.behavior_robot.set_robot(robot)
        self.world = world

    def deactivate(self):
        print("Behavior: Deactivated")
        self.robot = None
        self.behavior_robot.set_robot(None)
        self.world = None

        # stop network threads
        self.network_controller.exit()

    #
    # looping method
    #
    def next_speeds(self, robots, fish, timestep):

        if self.config["DEBUG"]["debug_charging"]:
            self.network_controller.charge_command.emit(
                {"command": "robot charging", "args": [0]}
            )

        # Move fish (simulate)
        if self.optimisation:
            start_time = time.time()

        # execute all commands in queue first
        while not (self.com_queue.empty()):
            command = self.com_queue.get()
            if self.config["DEBUG"]["console"]:
                print(command)
            try:
                func = getattr(self, command[0])
                args = command[1:]
                func(*args)
            except:
                print(f"Command not found or error in command execution! {command}")

        # TICK - update all fish one time step forward (tick)
        all_agents = [self.behavior_robot]
        all_agents.extend(self.allfish)
        all_pos = np.asarray([np.array(a.pos, dtype=np.float64) for a in all_agents])
        all_dir = np.asarray([a.dir for a in all_agents])
        dist_m = distance_matrix(all_pos, all_pos)

        for id_f, f in enumerate(all_agents):
            f.tick(all_pos, all_dir, dist_m[id_f])
            # check if fish following the robot
            if id_f != 0:
                robot_pos = all_pos[0]
                robot_dir = all_dir[0]
                f.check_following(robot_pos, robot_dir)

        # MOVE
        for f in all_agents:
            f.move()

        # Update fish in tracking view and send positions
        self.network_controller.update_positions.emit(self.serialize())

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

        return []

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
        # out.append([np.rint(self.behavior_robot.pos).tolist(), np.around(self.behavior_robot.ori, decimals=2), self.behavior_robot.id])
        robo_dict = {
            "id": self.behavior_robot.id,
            "orientation": np.around(self.behavior_robot.ori, decimals=2),
            "position": np.rint(self.behavior_robot.pos).tolist(),
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
        # print("New command queued!")

    #
    # Commands
    #
    # region <commands>
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

        # always set fish with id 1 to position 1500,500 if existing
        if len(self.allfish) > 0:
            if self.allfish[0].id == 1:
                self.allfish[0].pos = np.asarray([1500, 500])
            else:
                print("BEHAVIOR: Fish with id 1 not existing!")

        self.network_controller.update_ellipses.emit(self.behavior_robot, self.allfish)

    def control_robot(self, flag):
        self.behavior_robot.controlled = flag
        self.controlled = flag

        if not flag:
            self.behavior_robot.max_speed = self.config["DEFAULTS"]["max_speed"]

    def change_robodir(self, dir):
        # dir cannot be [0,0]
        if not (np.abs(dir) == np.asarray([0.0, 0.0])).all():
            np_dir = np.asarray(dir)
            dir_len = np.linalg.norm(np_dir)
            self.behavior_robot.max_speed = self.config["DEFAULTS"]["max_speed"] + 10
            self.behavior_robot.new_dir = (
                np_dir / dir_len if dir_len != 0 and dir_len > 1 else np_dir
            )
        else:
            self.behavior_robot.max_speed = 0

    def change_zones(self, zone_dir):
        self.zor = zone_dir.get("zor", self.zor)
        self.zoo = zone_dir.get("zoo", self.zoo)
        self.zoa = zone_dir.get("zoa", self.zoa)

        self.behavior_robot.change_zones(self.zor, self.zoo, self.zoa)
        for f in self.allfish:
            f.change_zones(self.zor, self.zoo, self.zoa)

        if self.debug_vis:
            self.network_controller.update_ellipses.emit(
                self.behavior_robot, self.allfish
            )

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

        if size == 2:
            self.zor = self.config["ZONE_MODES"]["CHALL"]["zor"]
            self.zoo = self.config["ZONE_MODES"]["CHALL"]["zoo"]
            self.zoa = self.config["ZONE_MODES"]["CHALL"]["zoa"]

        for f in self.allfish:
            f.change_zones(self.zor, self.zoo, self.zoa)

        if self.debug_vis:
            self.network_controller.update_ellipses.emit(
                self.behavior_robot, self.allfish
            )

        self.parameter_ui.zor_spinbox.setValue(self.zor)
        self.parameter_ui.zoo_spinbox.setValue(self.zoo)
        self.parameter_ui.zoa_spinbox.setValue(self.zoa)

    # endregion
