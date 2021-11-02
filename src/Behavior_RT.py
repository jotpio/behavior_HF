from logging import debug
import random, time, math, threading, queue, os, sys, logging
import numpy as np
import yaml  # pyyaml
from pathlib import Path
from scipy.spatial import distance_matrix
from collections.abc import Iterable
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))
# print(sys.path)

from src.ui.debug_visualization import DebugVisualization
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
from src.util.heartbeat import HeartbeatTimer

from src.util.serialize import serialize
from src.models.charging import *


from PyQt5.sip import wrapinstance as wrapInstance

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent, QTimer

import logging

FORMAT = "\t%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO)
numba_logger = logging.getLogger("numba")
numba_logger.setLevel(logging.WARNING)

try:
    from robotracker import (
        PythonBehavior,
        RobotActionFlush,
        RobotActionHalt,
        RobotActionToTarget,
        RobotActionDirect,
        RobotActionTurningForward,
    )

    RT_MODE = True
except:
    print("No RoboTracker found!")
    RT_MODE = False

np.warnings.filterwarnings("error", category=np.VisibleDeprecationWarning)


class Behavior(PythonBehavior):
    def __init__(self, layout=None, DEBUG_VIS=None, config=None):
        PythonBehavior.__init__(self)

        self.robot = None
        self.world = None
        self.target = None

        # load config
        self.config = config
        if self.config is None:
            path = (Path(__file__).parents[1]) / "cfg/config.yml"
            print(f"Behavior: config path: {path}")
            self.config = yaml.safe_load(open(path))

        # setup logging
        formatter = logging.Formatter(
            "\t%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        logger = logging.getLogger()
        handler = TimedRotatingFileHandler(
            Path.home() / self.config["LOGGING"]["BEHAVIOR"], when="H", interval=1
        )
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)

        # setup util
        self.util = Util(self.config)

        #
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

        # heartbeat
        self.heartbeat_obj = HeartbeatTimer(self.config)
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_obj.run_thread)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

        # logging
        self.setup_logging()

        # arena
        self.arena = Arena(
            [0, 0], self.config["ARENA"]["width"], self.config["ARENA"]["height"]
        )

        # initialize robot
        self.behavior_robot = Robot(self.arena, self.config)
        # self.controlled = False
        self.trigger_next_robot_step = False
        self.flush_robot_target = False
        self.action = []
        self.just_started = False

        # charger positions
        self.charger_pos = self.config["CHARGER"]["position"]
        charger_target = self.charger_pos[0] + 200, self.charger_pos[1]
        self.charger_target = self.util.map_px_to_cm(charger_target)

        # # initialize fish
        self.reset_fish(self.config["DEFAULTS"]["number_of_fish"])

        self.initiate_numba()

        # setup debug viz
        self.debug_vis = DEBUG_VIS
        if DEBUG_VIS is None and self.config["DEBUG"]["visualisation"]:
            self.debug_vis = DebugVisualization(self.config)
            self.network_controller.update_ellipses.connect(
                self.debug_vis.update_ellipses, Qt.QueuedConnection
            )
            self.network_controller.update_positions.connect(
                self.debug_vis.update_view, Qt.QueuedConnection
            )
            self.network_controller.update_ellipses.emit(
                self.behavior_robot, self.allfish
            )

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

        # setup debug vis
        if self.debug_vis is not None:
            self.setup_debug_vis()

        # step logger
        self._step_logger = []
        self.exec_time = 0
        self.exec_stepper = 0

        # setup command queue
        self.com_queue = queue.LifoQueue()

        self.movelist = []

        self.turn_left = False
        self.turn_right = False

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
            np.asarray([1.4, 2.0, 43.0321, 4214.3123, 2.3]),
            np.zeros((5, 2)),
            np.zeros((5, 2)),
            10,
            50,
            150,
        )
        normalize(np.asarray([1.4, 2.0]))

    def setup_logging(self):
        now = datetime.now()
        formatter = logging.Formatter("%(asctime)s -8s %(message)s")
        self.fish_logger = logging.getLogger("fish_logger")
        fish_handler = TimedRotatingFileHandler(
            Path.home() / self.config["LOGGING"]["FISH"], when="H", interval=1
        )
        fish_handler.setFormatter(formatter)
        # handler.setLevel(logging.CRITICAL)
        self.fish_logger.addHandler(fish_handler)
        self.fish_logger.warning(f"Started a new behavior: {now}")

        self.logcounter = 0

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

    def supported_timesteps(self):
        print("Behavior: supported_timesteps called")
        return []

    def activate(self, robot, world):
        print("Behavior: Activated")
        self.robot = robot
        self.behavior_robot.set_robot(robot)
        self.world = world
        self.just_started = True

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

        # at start go to middle of arena
        try:
            if self.just_started:
                # check if close to charging station first and drive away in charging routine
                close_to_ch_st = check_if_close_to_charging_station(
                    self.behavior_robot, self.charger_pos
                )
                if not close_to_ch_st:
                    middle_pos = [self.arena.width / 2, self.arena.height / 2]
                    middle_pos_cm = self.util.map_px_to_cm(middle_pos)
                    if not self.action:
                        self.action = [
                            RobotActionFlush(self.robot.uid),
                            RobotActionToTarget(
                                self.robot.uid, 0, (middle_pos_cm[0], middle_pos_cm[1])
                            ),
                        ]
                    # check if roughly at middle pos then robot is free
                    diff = np.abs(np.asarray(middle_pos) - self.behavior_robot.pos)
                    if diff[0] < 100 and diff[1] < 100:
                        self.just_started = False
                    else:
                        print(f"\nBEHAVIOR: In robot starting routine!!!!\n")
        except Exception as e:
            print(f"\nBEHAVIOR: Error in start movement")
            print(e)

        try:
            if self.optimisation:
                start_time = time.time()

            try:
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
                        print(
                            f"Command not found or error in command execution! {command}"
                        )
            except:
                print(f"\nBEHAVIOR: Error in command queue")

            # update behavior robot position, voltage, dir and ori if RT loaded
            try:
                if RT_MODE:
                    robots = [r for r in robots if r.uid == self.robot.uid]
                    self.behavior_robot.set_attributes(robots[0])
            except:
                print(f"\nBEHAVIOR: Error in robot update")

            try:
                # check for flush robot target triggered
                if self.flush_robot_target and not self.action:
                    self.flush_robot_target = False
                    self.action = [
                        RobotActionFlush(self.robot.uid),
                        RobotActionHalt(self.robot.uid, 0),
                    ]

                # no robot then send halt
                if not robots and not self.action:
                    self.action = [
                        RobotActionFlush(self.robot.uid),
                        RobotActionHalt(self.robot.uid, 0),
                    ]
                else:
                    # charging routine
                    charging_action = charging_routine(
                        robots[0],
                        self.behavior_robot,
                        self.action,
                        self.charger_pos,
                        self.network_controller,
                        self.charger_target,
                    )
                    if charging_action != []:
                        self.action = charging_action

                    # robot control buttons
                    if self.target is not None:
                        print(f"Set target to {self.target}")
                        target = self.target
                        self.target = None
                        if not self.action:
                            self.action = [
                                RobotActionFlush(self.robot.uid),
                                RobotActionToTarget(
                                    self.robot.uid, 0, (target[0], target[1])
                                ),
                            ]
                    if self.turn_left and not self.action:
                        self.action = [
                            RobotActionDirect(self.robot.uid, 0, 0.0, 5.0),
                        ]

                    if self.turn_right and not self.action:
                        self.action = [
                            RobotActionDirect(self.robot.uid, 0, 5.0, 0.0),
                        ]
            except Exception as e:
                print(f"\nBEHAVIOR: Error in robot priority actions/ charging behavior")
                print(e)

            # TICK - update all fish one time step forward (tick)
            try:
                all_agents = [self.behavior_robot]
                all_agents.extend(self.allfish)
                all_pos = np.asarray(
                    [np.array(a.pos, dtype=np.float64) for a in all_agents]
                )
                all_dir = np.asarray([a.dir for a in all_agents])
                dist_m = distance_matrix(all_pos, all_pos)

                for id_f, f in enumerate(all_agents):
                    f.tick(all_pos, all_dir, dist_m[id_f])
                    # check if fish following the robot
                    if id_f != 0:
                        robot_pos = all_pos[0]
                        robot_dir = all_dir[0]
                        f.check_following(robot_pos, robot_dir)
            except:
                print(f"\nBEHAVIOR: Error in tick")

            # MOVE - move everything by new updated direction and speed
            try:
                try:
                    for f in all_agents:
                        f.move()
                except:
                    print(f"\nBEHAVIOR: Error in all agents move")

                if (
                    not self.behavior_robot.charging
                    and not self.behavior_robot.go_to_charging_station
                ):
                    if RT_MODE:
                        if not self.behavior_robot.controlled:
                            try:

                                # get new robot target and move there
                                target = self.util.map_px_to_cm(
                                    self.behavior_robot.target_px
                                )
                                # print(f"ROBOT: new cm target: {target}")

                                if not self.action:
                                    self.action = [
                                        RobotActionFlush(self.robot.uid),
                                        RobotActionToTarget(
                                            self.robot.uid, 0, (target[0], target[1])
                                        ),
                                    ]
                            except:
                                print(
                                    f"nBEHAVIOR: Error in move - automatic robot movement"
                                )

                        elif self.trigger_next_robot_step:
                            try:
                                # move to next target on pushbutton press
                                target = self.util.map_px_to_cm(
                                    self.behavior_robot.target_px
                                )
                                print(
                                    f"Move robot to new location: {self.behavior_robot.pos}\ntarget px: {self.behavior_robot.target_px}\ntarget cm: {target}\ndir: {self.behavior_robot}\nrobot dir: {robots[0].orientation}"
                                )
                                if not self.action:
                                    self.action = [
                                        RobotActionFlush(self.robot.uid),
                                        RobotActionToTarget(
                                            self.robot.uid,
                                            0,
                                            (target[0], target[1]),
                                        ),
                                    ]
                                self.trigger_next_robot_step = False
                            except:
                                print(
                                    f"\nBEHAVIOR: Error in move - trigger_next_robot_step"
                                )

            except:
                print(f"\nBEHAVIOR: Error in move")

            # Update fish in tracking view and send positions
            serialized = serialize(self.behavior_robot, self.allfish)
            self.network_controller.update_positions.emit(serialized)

            # log direction every few ticks
            if self.logcounter == 5 and self.behavior_robot.user_controlled:
                self.fish_logger.warning(f"{serialized}")
                self.logcounter = 0
            self.logcounter += 1

            # print("end of next speeds")

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
            return_action = self.action
            self.action = []

            return return_action
        except Exception as e:
            print(f"\nBEHAVIOR: Error in next_speeds!")
            print(e)

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
            self.allfish[0].pos = np.asarray([1500, 500])

        self.network_controller.update_ellipses.emit(self.behavior_robot, self.allfish)

    def control_robot(self, flag):
        self.behavior_robot.controlled = flag
        self.controlled = flag

    def change_robodir(self, dir):
        np_dir = np.asarray(dir)

        self.behavior_robot.new_dir = normalize(np_dir)
        self.behavior_robot.user_controlled = True

        # dir_len = np.linalg.norm(np_dir)
        # self.behavior_robot.new_dir = (
        #     np_dir / dir_len if dir_len != 0 else np.asarray([0, 0])
        # )

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
