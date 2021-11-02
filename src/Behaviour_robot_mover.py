import sys
import yaml
import threading

from PyQt5.QtWidgets import QLayout, QVBoxLayout, QPushButton
from PyQt5.sip import wrapinstance as wrapInstance

from pathlib import Path

path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))
# logging.error(sys.path)

try:
    from robotracker import (
        PythonBehavior,
        RobotActionFlush,
        RobotActionHalt,
        RobotActionToTarget,
    )

    print("RoboTracker found!")
except:
    print("No RoboTracker found!")

from net.robot_command_listener_server import RobotCommandListenerServer
from net.robot_attribute_client import RobotAttributeClient


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

        # next_command
        self.next_received_command = None
        self.next_robot_command = None

    # def on_random_target_clicked(self):
    #     self.target = random.randint(10, 55), random.randint(10, 55)
    #     print(f"New target selected: {self.target[0]},{self.target[1]}")

    def set_next_command(self, command):
        print(command)

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

    def next_speeds(self, robots, fish, timestep):
        robots = [r for r in robots if r.uid == self.robot.uid]

        action = []

        if not robots:
            print("No robot found!")
            action = [
                RobotActionFlush(self.robot.uid),
                RobotActionHalt(self.robot.uid, 0),
            ]
        else:

            # send new attributes to simulation
            self.robot_attribute_client.send_robot_attributes(robots[0])

            # execute current command
            if self.next_robot_command is not None:
                print(f"Next robot command: {self.next_robot_command}")
                action = self.next_robot_command
                self.next_robot_command = None
            else:
                print(f"No new robot command!")

        return action
