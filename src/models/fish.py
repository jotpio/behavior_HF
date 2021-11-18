import math, random
import logging, os, sys
import numpy as np
from src.models.arena import Arena
from src.models.agent import Agent
from PyQt5.QtCore import *
import time


class Fish(Agent):
    def __init__(
        self,
        id,
        pos,
        ori,
        arena,
        config,
        dir=None,
        zoa=None,
        zoo=None,
        zor=None,
        time_step=None,
    ):
        super().__init__(id, pos, ori, arena, config, dir, zor, zoo, zoa, time_step)

        # self.aligned_with_robot = False
        self.follow_angle = self.config["DEFAULTS"]["follow_angle"]
        self.follow_angle_cos = np.cos(np.radians(self.follow_angle))
        self.following = False
        self.cos_max_turn_per_time_step = np.cos(
            np.radians(self.max_turn_rate * self.time_step * 10)
        )

    def check_following(self, robot_pos, robot_dir):
        try:
            # robot in attaction zone
            if self.influenced_by_robot:
                # check if robot swims in same direction as fish
                # orientation difference can't be larger than max turning rate * 10 (roughly same direction)
                # calculate angle between both directions
                inner = np.inner(self.dir, robot_dir)
                norms = np.linalg.norm(self.dir) * np.linalg.norm(robot_dir)
                ori_diff = inner / norms
                roughly_same_dir = ori_diff >= self.cos_max_turn_per_time_step

                # robot must be in front of fish
                # cos of angle between (robot_pos-self.pos) vector and self.dir cannot be smaller than 0 (angle can't be larger than pi/2 -> 90degrees) / smaller than 60 -> cos(radians(80)) = 0.17365152758
                between_v = robot_pos - self.pos
                inner = np.inner(between_v, self.dir)
                norms = np.linalg.norm(between_v) * np.linalg.norm(self.dir)
                ori_diff2 = inner / norms
                in_front = ori_diff2 > self.follow_angle_cos

                if roughly_same_dir and in_front:
                    self.following = True
                    return
            self.following = False
        except Exception as e:
            logging.error("FISH: Error while following check")
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(exc_type, fname, exc_tb.tb_lineno)
