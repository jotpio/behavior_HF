import sys
import yaml
import threading
import os.path
import numpy as np

from PyQt5.QtWidgets import QLayout, QVBoxLayout, QPushButton
from PyQt5.sip import wrapinstance as wrapInstance

from pathlib import Path

from util.heartbeat import HeartbeatTimer
from util.util import Util

path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))
# logging.error(sys.path)

try:
    from robotracker import (
        PythonBehavior,
        RobotActionFlush,
        RobotActionHalt,
        RobotActionToTarget,
        RobotActionDirect,
    )

    print("RoboTracker found!")
except:
    print("No RoboTracker found!")

from net.robot.robot_command_listener_server import RobotCommandListenerServer
from net.robot.robot_attribute_client import RobotAttributeClient


class Behavior(PythonBehavior):
    def __init__(self, layout):
        PythonBehavior.__init__(self)

        self.parent_layout = wrapInstance(layout, QLayout)
        self.layout = QVBoxLayout()

        # Example for custom GUI
        random_target = QPushButton(f"This button does nothing")
        # random_target.clicked.connect(self.on_random_target_clicked)
        self.layout.addWidget(random_target)
        self.parent_layout.addLayout(self.layout)

        self.robot = None
        self.world = None
        self.target = None

        # load config
        path = (Path(__file__).parents[1]) / "cfg/config.yml"
        print(f"BEHAVIOR: config path: {path}")
        self.config = yaml.safe_load(open(path))

        # networking
        self.robot_command_listener_server = RobotCommandListenerServer(
            self, config=self.config
        )
        self.robot_attribute_client = RobotAttributeClient(self, config=self.config)

        self.rcls_thread = threading.Thread(
            target=self.robot_command_listener_server.run_thread
        )
        self.rcls_thread.daemon = True
        self.rcls_thread.start()

        self.rac_thread = threading.Thread(
            target=self.robot_attribute_client.run_thread
        )
        self.rac_thread.daemon = True
        self.rac_thread.start()

        # heartbeat
        self.heartbeat_obj = HeartbeatTimer(self.config)
        self.heartbeat_obj.heartbeat_path = (
            "/home/user1/RoboTracker_HF/heartbeat/RT_mover_Log.txt"
        )
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_obj.run_thread)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

        # next_command
        self.last_robot_command = None
        self.next_received_command = None
        self.next_robot_command = None
        self.direct = False

        # shutdown routine
        self.shutdown_routine = False
        self.shutdown_trigger_path = self.config["SHUTDOWN"]["PATH"]
        self.shutdown_charging_path = self.config["SHUTDOWN"]["CHARGING_PATH"]

        # util
        self.util = Util(self.config)

        # charger positions
        self.charger_pos = self.config["CHARGER"]["position"]
        charger_target = self.charger_pos[0] + 200, self.charger_pos[1]
        self.charger_target = self.util.map_px_to_cm(charger_target)

    # def on_random_target_clicked(self):
    #     self.target = random.randint(10, 55), random.randint(10, 55)
    #     print(f"New target selected: {self.target[0]},{self.target[1]}")

    def set_next_command(self, command):
        try:
            self.next_received_command = command
            robot_command = []
            for c in command:
                if c[0] == "flush":
                    self.direct = False
                    robot_command.append(RobotActionFlush(*c[1]))
                elif c[0] == "halt":
                    self.direct = False
                    robot_command.append(RobotActionHalt(*c[1]))
                elif c[0] == "target":
                    self.direct = False
                    robot_command.append(RobotActionToTarget(*c[1]))
                elif c[0] == "direct":
                    if not self.direct:
                        robot_command.append(
                            RobotActionFlush(c[1][0])
                        )  # flush last commands if direct movement is starting
                        self.direct = True
                    robot_command.append(RobotActionDirect(*c[1]))

            # print(robot_command)
            self.next_robot_command = robot_command
        except Exception as e:
            print("Error in parsing next command")
            print(e)

    def supported_timesteps(self):
        return []

    def activate(self, robot, world):
        print("Behavior: Activated")
        self.robot = robot
        self.world = world

    def deactivate(self):
        print("Behavior: Deactivated")
        self.robot = None
        self.world = None

        self.robot_attribute_client.close_socket()
        self.robot_command_listener_server.close_socket()

    def next_speeds(self, robots, fish, timestep):
        robots = [r for r in robots if r.uid == self.robot.uid]

        action = []

        # print(robots[0].action_list)

        if not robots:
            print("No robot found!")
            action = [
                RobotActionFlush(self.robot.uid),
                RobotActionHalt(self.robot.uid, 0),
            ]
            # send no robot to simulation
            self.robot_attribute_client.send_robot_attributes(None)

        else:
            # check if robot shutdown routine is initialized
            self.shutdown_routine = os.path.isfile(self.shutdown_trigger_path)
            if not self.shutdown_routine:

                # send new attributes to simulation
                self.robot_attribute_client.send_robot_attributes(robots[0])

                # execute current command
                if self.next_robot_command is not None:
                    # print(f"Next robot command: {self.next_robot_command}")
                    action = self.next_robot_command
                    self.last_robot_command = self.next_robot_command
                    self.next_robot_command = None
                elif self.direct:
                    action = self.last_robot_command
                else:
                    # print(f"No new robot command!")
                    pass
            else:
                action = self.shutdown_routine(robots[0])
                # send no robot to simulation
                self.robot_attribute_client.send_robot_attributes(None)

        return action

    def shutdown_routine(self, robot):
        # send no robot to simulation
        self.robot_attribute_client.send_robot_attributes(None)

        print("Charging routine: go to charging station")

        # check if at right y position in front of charger
        pos = robot.pos
        pos_y_difference = np.abs(pos[1] - self.charger_pos[1])
        if pos_y_difference < 50:
            right_posy = True
        else:
            right_posy = False
        # go to right position in front of charger
        if not right_posy:
            action = [
                ["flush", [robot.uid]],
                [
                    "target",
                    [robot.uid, 0, (self.charger_target[0], self.charger_target[1]),],
                ],
            ]
            return action

        print("Robot at right y pos")

        # check rotation
        rot = robot.ori
        right_rot = np.abs(rot) > 175
        # rotate until correct orientation
        if not right_rot:
            action = [
                ["direct", [robot.uid, 0, -7.0, -7.0]],
            ]
            return action
        print("Robot to charge and at right orientation")

        # drive forwards into charger
        # check first if at charger position
        pos_x_difference = pos[0] - self.charger_pos[0]
        if pos_x_difference <= 0:
            right_posx = True
        else:
            right_posx = False

        if not right_posx:
            # charger_pos = self.config["CHARGER"]["position"]
            # target = charger_pos[0], charger_pos[1]
            # target = self.util.map_px_to_cm(target)

            # drive slowly towards charger
            action = [
                ["direct", [robot.uid, 0, -7.0, -7.0]],
            ]
            return action
        print("Robot to charge and at right x pos!")

        if robot.chargingStatus:
            # if os.path.exists(self.shutdown_trigger_path):
            #     os.remove(self.shutdown_trigger_path)
            # else:
            #     print("Can not delete the file as it doesn't exists")
            Path(self.shutdown_charging_path).touch()

