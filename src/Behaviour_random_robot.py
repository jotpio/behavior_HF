import random

from PyQt5.QtWidgets import QLayout, QVBoxLayout, QPushButton
from PyQt5.sip import wrapinstance as wrapInstance

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


class Behavior(PythonBehavior):
    def __init__(self, layout):
        PythonBehavior.__init__(self)

        self.parent_layout = wrapInstance(layout, QLayout)
        self.layout = QVBoxLayout()

        # Example for custom GUI
        random_target = QPushButton(f"Drive to new random point")
        random_target.clicked.connect(self.on_random_target_clicked)
        self.layout.addWidget(random_target)
        self.parent_layout.addLayout(self.layout)

        self.robot = None
        self.world = None
        self.target = None
    
    def on_random_target_clicked(self):
        self.target = random.randint(10, 90), random.randint(10, 90)
        print(f"New target selected: {self.target[0]},{self.target[1]}")

    def supported_timesteps(self):
        return []

    def activate(self, robot, world):
        self.robot = robot
        self.world = world

    def deactivate(self):
        self.robot = None
        self.world = None

    def next_speeds(self, robots, fish, timestep):
        robots = [r for r in robots if r.uid == self.robot.uid]
        if not robots:
            print("No robot found!")
            return [
                RobotActionFlush(self.robot.uid),
                RobotActionHalt(self.robot.uid, 0),
            ]
        else:
            if self.target is not None:
                print(f"Target set: {self.target}")
                print(f"Robot: {self.robot.uid}")
                print(f"{self.robot.position}, {self.robot.orientation}")
                print(f"{robots[0].position}")
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
