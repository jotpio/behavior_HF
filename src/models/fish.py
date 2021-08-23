import math, random
import numpy as np
from src.models.arena import Arena
from src.models.agent import Agent
from PyQt5.QtCore import *
import time


class Fish(Agent):

    def __init__(self, id, pos, ori, arena, config, dir=None, zoa=None, zoo=None, zor=None, time_step=None):
        super().__init__(id, pos, ori, arena, config, dir, zoa, zoo, zor, time_step)

        self.following = False
        if self.id == 1 and self.config["DEBUG"]["debug_following"]:
            self.following = True