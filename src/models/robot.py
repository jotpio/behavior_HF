from src.models.agent import Agent
import numpy as np
import math


class Robot(Agent):
    def __init__(self, arena, config):
        super().__init__(0, [100, 100], 90, arena, config)

        self.controlled = config["ROBOT"]["controlled_from_start"]
        self.debug = False
        self.battery = 100
        self.new_dir = np.asarray([0.1, 0])
        self.real_robot = None

    def tick(self, fishpos, fishdir, dists):
        if self.debug:
            return
        if not self.controlled:
            super().tick(fishpos, fishdir, dists)

    def move(self):
        if self.debug:
            super().move()
        elif not self.controlled:
            super().move()
        else:
            super().move()

    def reload(self):
        print("ROBOT: Reloading...")
        pass

    def get_battery_charge(self):
        pass

    def set_robot(self, robot):
        self.real_robot = robot
        if robot:
            self.pos = np.asarray([robot.position[0], robot.position[1]])
            self.dir = np.asarray([robot.orientation[0], robot.orientation[1]])
            self.ori = np.degrees(math.atan2(self.dir[1], self.dir[0]))

            print(f"Behavior - Robot: {self.pos}")
