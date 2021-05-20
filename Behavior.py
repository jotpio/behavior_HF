import random

from PyQt5.sip import wrapinstance as wrapInstance
from PyQt5.QtWidgets import QLayout, QVBoxLayout, QHBoxLayout, QPushButton, QSpinBox, QLabel

from robotracker import (
    PythonBehavior,
    RobotActionFlush,
    RobotActionHalt,
    RobotActionToTarget,
)


class Behavior(PythonBehavior):
    def __init__(self, layout):
        PythonBehavior.__init__(self)

        self.parent_layout = wrapInstance(layout, QLayout)
        self.layout = QVBoxLayout()

        # Example for custom GUI
        random_target = QPushButton(f"Drive to new random point")
        random_target.clicked.connect(self.on_random_target_clicked)
        self.layout.addWidget(random_target)

        num_fish_layout = QHBoxLayout()
        num_fish_label = QLabel(f"Set number of fish:")
        num_fish_spinbox = QSpinBox(num_fish_layout)
        num_fish_spinbox.valueChanged.connect(self.on_num_fish_spinbox_valueChanged)
        num_fish_spinbox.setValue(4) #TODO: put this in config
        self.layout.addWidget(num_fish_label)
        self.layout.addWidget(num_fish_spinbox)

        self.parent_layout.addLayout(self.layout)

        self.robot = None
        self.world = None
        self.fish = [[random.randint(10, 90), random.randint(10, 90)] for i in range(num_fish_spinbox.value())]

        self._step_logger = []

    def on_random_target_clicked(self):
        self.target = random.randint(10, 90), random.randint(10, 90)
        print(f"New target selected: {self.target[0]},{self.target[1]}")

    def on_num_fish_spinbox_valueChanged(self, val):
        self.fish = [[random.randint(10, 90), random.randint(10, 90)] for i in range(val)]
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
        # log current positions to visualize in unity
        log_tuple = (timestep,) + tuple(robot_pose_gym) + tuple(self.fish)
        fish = None #flush fish


        # Move fish randomly (simulate)
        # TODO: make fish react with each other and robot
        
        #
        


        # Move robots randomly
        # TODO: make robots interact with fish 
        robots = [r for r in robots if r.uid == self.robot.uid]
        if not robots:
            return [
                RobotActionFlush(self.robot.uid),
                RobotActionHalt(self.robot.uid, 0),
            ]
        else:
            if self.target is not None:
                target = self.target
                self.target = None
                return [
                    RobotActionFlush(self.robot.uid),
                    RobotActionToTarget(
                        self.robot.uid, 0, (target[0], target[1])
                    ),
                ]
            else:
                return []



