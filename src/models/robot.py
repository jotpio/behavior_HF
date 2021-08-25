from src.models.agent import Agent
import numpy as np


class Robot(Agent):
    def __init__(self, arena, config):
        super().__init__(0, [100, 100], 90, arena, config)

        self.controlled = config["ROBOT"]["controlled_from_start"]
        self.debug = False
        self.battery = 100
        self.new_dir = np.asarray([0.1, 0])

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
        pass

    def get_battery_charge(self):
        pass

