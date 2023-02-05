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
from src.models.charging import charging_routine

import random
import time
import threading
import queue
import os
import sys
import logging
import numpy as np
import yaml  # pyyaml
from pathlib import Path
from scipy.spatial import distance_matrix
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject


FORMAT = "\t%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# setup logging
logging.basicConfig(format=FORMAT, level=logging.INFO)
numba_logger = logging.getLogger("numba")
numba_logger.setLevel(logging.WARNING)

np.warnings.filterwarnings("error", category=np.VisibleDeprecationWarning)


class Behavior(QObject):
    """
    Controller class of the simulation. In the event loop, it handles the agents movement and manages the robot.
    This class connects to RoboTracker and Unity, and sends RobotActions, agent positions
    """

    def __init__(self, layout=None, DEBUG_VIS=None, config=None):
        super().__init__()

        self.world = None
        self.target = None

        self.parameter_ui = None

        # load config
        self.config = config
        if self.config is None:
            path = (Path(__file__).parents[1]) / "cfg/config.yml"
            logging.info(f"BEHAVIOR: config path: {path}")
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

        self.util = Util(self.config)
        self.debug_vis = DEBUG_VIS

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
        self.heartbeat_obj = HeartbeatTimer(config)
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_obj.run_thread)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

        # logging
        self.setup_logging()

        # arena
        self.arena = Arena(
            [0, 0], self.config["ARENA"]["width"], self.config["ARENA"]["height"]
        )
        self.middle_pos = [self.arena.width / 2, self.arena.height / 2]
        self.middle_pos_cm = self.util.map_px_to_cm(self.middle_pos)

        # initialize robot
        self.behavior_robot = Robot(self.arena, self.config)
        # self.controlled = False
        self.trigger_next_robot_step = False
        self.flush_robot_target = False
        self.action = []
        self.just_started = False

        # charger positions
        self.charger_pos = self.config["CHARGER"]["position"]
        charger_target = self.charger_pos[0] - 300, self.charger_pos[1]
        self.charger_target = self.util.map_px_to_cm(charger_target)

        # initialize fish
        self.reset_fish(self.config["DEFAULTS"]["number_of_fish"])

        # numba
        self.initiate_numba()

        self.parent_layout = (
            layout if self.debug_vis is not None else self.setup_parameter_layout()
        )

        self.setup_parameter_ui()  # fill parameter layout

        # step logger
        self._step_logger = []
        self.exec_time = 0
        self.exec_stepper = 0

        # setup command queue
        self.com_queue = queue.LifoQueue()

        # setup debug vis
        if self.debug_vis is not None:
            self.setup_debug_vis()

        # catch key events
        if self.debug_vis is not None:
            app = QApplication.instance()
            app.installEventFilter(self)
        self.movelist = []

        self.turn_left = False
        self.turn_right = False

        logging.info("Behavior: Initialized!")

    def initiate_numba(self) -> None:
        """
        Initially executes reused functions sped up by JIT compiler numba
        """
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
            np.asarray([1.4, 2.0, 43.0321, 4214.3123, 2.5]),
            np.zeros((5, 2)),
            np.zeros((5, 2)),
            10,
            50,
            150,
        )
        normalize(np.asarray([1.4, 2.0]))

    def setup_logging(self) -> None:
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
        self.fish_logger.propagate = False

        self.logcounter = 0

    def setup_parameter_layout(self):
        logging.info("Behavior: Setting up parameter layout")
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

    def setup_debug_vis(self) -> None:
        self.debug_vis.setArena(self.arena)

    def setup_parameter_ui(self) -> None:
        logging.info("Behavior: Setting up parameter ui")
        self.parameter_ui = Parameter_UI(self, False, self.config)
        #
        self.parent_layout.addLayout(self.parameter_ui)

    def next_speeds(self) -> None:
        """
        looping method:
            - received commands are executed
            - the simulation agents are managed
            - the robot movement is translated to RoboTracker Actions
        """
        try:
            if self.optimisation:
                start_time = time.time()

            try:
                # execute all commands in queue first
                while not (self.com_queue.empty()):
                    command = self.com_queue.get()
                    if self.config["DEBUG"]["console"]:
                        logging.info(command)
                    try:
                        func = getattr(self, command[0])
                        args = command[1:]
                        func(*args)
                    except Exception as e:
                        logging.error(
                            f"BEHAVIOR: Command not found or error in command execution! {command}"
                        )
                        logging.error(e)
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                        logging.error(exc_type, fname, exc_tb.tb_lineno)

            except Exception as e:
                logging.error(f"BEHAVIOR: Error in command queue")
                logging.error(e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                logging.error(exc_type, fname, exc_tb.tb_lineno)

            # robot priority actions (incl. charging behavior)
            try:
                # check for flush robot target triggered
                if self.flush_robot_target and not self.action:
                    self.flush_robot_target = False
                    self.action = [
                        ["flush", [self.behavior_robot.uid]],
                        ["halt", [self.behavior_robot.uid, 0]],
                    ]

                # no robot then send halt
                if not self.behavior_robot.real_robot and not self.action:
                    self.action = [
                        ["flush", [self.behavior_robot.uid]],
                        ["halt", [self.behavior_robot.uid, 0]],
                    ]
                else:
                    # charging routine
                    charging_action = charging_routine(
                        self.behavior_robot,
                        self.action,
                        self.charger_pos,
                        self.network_controller,
                        self.charger_target,
                    )
                    if charging_action != []:
                        self.action = charging_action
                        logging.info(f"Currently using charging action!")

                    # robot control buttons
                    if self.target is not None:
                        logging.info(f"Set target to {self.target}")
                        target = self.target
                        self.target = None
                        if not self.action:
                            self.action = [
                                ["flush", [self.behavior_robot.uid]],
                                [
                                    "target",
                                    [
                                        self.behavior_robot.uid,
                                        0,
                                        (target[0], target[1]),
                                    ],
                                ],
                            ]
                    if self.turn_left and not self.action:
                        self.action = [
                            ["direct", [self.behavior_robot.uid, 0, 0.0, 5.0]],
                        ]

                    if self.turn_right and not self.action:
                        self.action = [
                            ["direct", [self.behavior_robot.uid, 0, 0.0, 5.0]],
                        ]

            except Exception as e:
                logging.error(
                    f"BEHAVIOR: Error in robot priority actions/ charging behavior"
                )
                logging.error(e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                logging.error(exc_type, fname, exc_tb.tb_lineno)

            #
            # TICK - update all fish one time step forward (tick)
            #
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
            except Exception as e:
                logging.error(f"BEHAVIOR: Error in tick")
                logging.error(e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                logging.error(exc_type, fname, exc_tb.tb_lineno)

            #
            # MOVE - move everything by new updated direction and speed
            #
            try:
                try:
                    for f in all_agents:
                        f.move()
                except Exception as e:
                    logging.error(f"BEHAVIOR: Error in all agents move")
                    logging.error(e)
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    logging.error(exc_type, fname, exc_tb.tb_lineno)

                if True:  # TODO
                    # automatic movement
                    if (
                        not self.behavior_robot.controlled
                        and not self.behavior_robot.user_controlled
                    ):
                        try:
                            # get new robot target and move there
                            target = self.util.map_px_to_cm(
                                self.behavior_robot.target_px
                            )

                            if not self.action:
                                self.action = [
                                    ["flush", [self.behavior_robot.uid]],
                                    [
                                        "target",
                                        [
                                            self.behavior_robot.uid,
                                            0,
                                            (
                                                target[0],
                                                target[1],
                                            ),
                                        ],
                                    ],
                                ]
                        except Exception as e:
                            logging.error(
                                f"BEHAVIOR: Error in move - automatic robot movement"
                            )
                            logging.error(e)
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                            logging.error(exc_type, fname, exc_tb.tb_lineno)
                    # next step clicked
                    elif self.trigger_next_robot_step:
                        try:
                            # move to next target on pushbutton press
                            target = self.util.map_px_to_cm(
                                self.behavior_robot.target_px
                            )
                            logging.info(
                                f"Move robot to new location: {self.behavior_robot.pos}\ntarget px: {self.behavior_robot.target_px}\ntarget cm: {target}\ndir: {self.behavior_robot}\nrobot ori: {self.behavior_robot.ori}"
                            )
                            if not self.action:
                                self.action = [
                                    ["flush", [self.behavior_robot.uid]],
                                    [
                                        "target",
                                        [
                                            self.behavior_robot.uid,
                                            0,
                                            (
                                                target[0],
                                                target[1],
                                            ),
                                        ],
                                    ],
                                ]
                            self.trigger_next_robot_step = False
                        except Exception as e:
                            logging.error(
                                f"BEHAVIOR: Error in move - trigger_next_robot_step"
                            )
                            logging.error(e)
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                            logging.error(exc_type, fname, exc_tb.tb_lineno)
                    # joystick movement
                    elif self.behavior_robot.user_controlled:
                        try:
                            # get new robot target and move there
                            target = self.util.map_px_to_cm(
                                self.behavior_robot.target_px
                            )
                            # logging.info(f"ROBOT: joystick target: {target}")

                            if not self.action:
                                self.action = [
                                    ["flush", [self.behavior_robot.uid]],
                                    [
                                        "target",
                                        [
                                            self.behavior_robot.uid,
                                            0,
                                            (
                                                target[0],
                                                target[1],
                                            ),
                                        ],
                                    ],
                                ]
                        except Exception as e:
                            logging.error(
                                f"nBEHAVIOR: Error in move - joystick robot movement"
                            )
                            logging.error(e)
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                            logging.error(exc_type, fname, exc_tb.tb_lineno)

                    else:
                        print("none of the above")

            except Exception as e:
                logging.error(f"BEHAVIOR: Error in move")
                logging.error(e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                logging.error(exc_type, fname, exc_tb.tb_lineno)

            # done with behavior simulation

            # Update fish in tracking view and send positions
            serialized = serialize(self.behavior_robot, self.allfish)
            self.network_controller.update_positions.emit(serialized)

            # log fish every few ticks when user controlled
            if self.behavior_robot.user_controlled:
                if self.logcounter == 5:
                    self.fish_logger.info(f"{serialized}")
                    self.logcounter = 0
                self.logcounter += 1

            if self.optimisation:
                end_time = time.time()
                exec_time = end_time - start_time

                if self.exec_stepper == 100:
                    self.exec_stepper = 0
                    self.exec_time = 0
                self.exec_stepper += 1
                self.exec_time += exec_time
                mean_exec_time = self.exec_time / self.exec_stepper
                logging.info(
                    f"mean tick takes {mean_exec_time} seconds; last tick took {exec_time} seconds"
                )

            # send robot action to RoboTracker
            return_action = [
                ["flush", [self.behavior_robot.uid]],
                ["halt", [self.behavior_robot.uid, 0]],
            ]
            if (
                not self.behavior_robot.stop
                or self.behavior_robot.go_to_charging_station
                or self.behavior_robot.charging
            ):
                return_action = self.action

            self.action = []

            self.network_controller.robot_command_client.send_robot_command(
                return_action
            )

        except Exception as e:
            logging.error(f"BEHAVIOR: Error in next_speeds!")
            logging.error(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(exc_type, fname, exc_tb.tb_lineno)

    def run_thread(self) -> None:
        step = 0
        while True:
            self.next_speeds()
            step += 1
            time.sleep(self.time_step)

    def __del__(self):
        pass

    def app_exec(self):
        sys.exit(self.app.exec_())

    def serialize(self) -> list:
        out = []
        # robot
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

    def queue_command(self, command) -> None:
        self.com_queue.put((command[0], command[1]))

    #
    # Commands
    #
    # region <commands>
    def reset_fish(self, num) -> None:
        """
        Receive position reset for current fish
        """
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
                logging.error("BEHAVIOR: Fish with id 1 not existing!")

        self.network_controller.update_ellipses.emit(self.behavior_robot, self.allfish)
        if self.parameter_ui:
            self.parameter_ui.num_fish_spinbox.setValue(num)

    def control_robot(self, flag) -> None:
        """
        Receive robot user control trigger
        """
        self.behavior_robot.controlled = flag
        self.controlled = flag
        self.behavior_robot.user_controlled = flag

        if not flag:
            self.behavior_robot.max_speed = self.config["DEFAULTS"]["max_speed"]
            self.behavior_robot.stop = False

    def change_robodir(self, dir) -> None:
        """
        - receives joystick input and translates it into robot direction
        - dir cannot be [0,0]
        """
        if not (np.abs(dir) == np.asarray([0.0, 0.0])).all():
            self.behavior_robot.stop = False
            np_dir = np.asarray(dir)
            dir_len = np.linalg.norm(np_dir)
            self.behavior_robot.max_speed = self.config["DEFAULTS"]["max_speed"] + 10
            self.behavior_robot.new_dir = (
                np_dir / dir_len if dir_len != 0 and dir_len > 1 else np_dir
            )
        else:
            self.behavior_robot.max_speed = 0
            self.behavior_robot.stop = True

    def set_next_attribute(self, robot) -> None:
        """
        Receives tracked robot pose from RoboTracker
        """
        try:
            # no robot found by robotracker
            if "no robot" in robot:
                logging.warning("BEHAVIOR: No robot received! Using simulated robot")
                self.behavior_robot.real_robot = None
            else:
                if (
                    self.behavior_robot.real_robot is None
                    and not self.behavior_robot.charging
                    and not self.behavior_robot.go_to_charging_station
                ):
                    logging.warning("BEHAVIOR: New robot connected! Using real robot")
                    self.behavior_robot.set_robot(robot)
                # logging.info(f"BEHAVIOR:  {robot}")
                self.behavior_robot.set_attributes(robot)
        except Exception as e:
            logging.error("BEHAVIOR: Error in robot attribute update")
            logging.error(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(exc_type, fname, exc_tb.tb_lineno)

    def change_zones(self, zone_dir) -> None:
        """
        Change zone radii for all agents
        """
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
        """
        Change zone radii for all agents to preset
        """
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

    def set_speed(self, speed) -> None:
        """
        Set speed of all fish
        """
        for f in self.allfish:
            if f.id != 0:
                f.max_speed = speed

    def challenge_status(self, toggle):
        """
        Receive challenge status update
        """
        status = "started!" if toggle == 1 else "stopped!"
        logging.info(f"Challenge {status}")

    # endregion
