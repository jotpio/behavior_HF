from src.models.agent import Agent, normalize
import numpy as np
import math
import time
from datetime import datetime
from collections import deque
from PyQt5.QtCore import *
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from src.util.util import Util
import os, sys


class LeaderRobot(Agent):
    def __init__(self, arena, config):
        super().__init__(0, [1000, 1000], 90, arena, config)

        self.uid = 0
        self.util = Util(self.config)

        self.controlled = config["ROBOT"]["controlled_from_start"]
        self.debug = False

        self.new_dir = np.asarray([0.00001, 0])
        self.real_robot = False
        self.target_px = [0, 0]
        self.user_controlled = False
        self.stop = False
        self.arena_repulsion = self.config["ROBOT"]["arena_repulsion"]

        # zone radii
        self.zor = config["ROBOT"]["zor"]
        self.zoo = config["ROBOT"]["zoo"]
        self.zoa = config["ROBOT"]["zoa"]

        self.max_turn_rate = self.config["ROBOT"]["max_turn_rate"]
        self.error_deg = self.config["ROBOT"]["error_deg"]

        self.setup_logging()

    def setup_logging(self):
        now = datetime.now()
        formatter = logging.Formatter("%(asctime)s -8s %(message)s")

        self.logger = logging.getLogger("robot_logger")
        handler = TimedRotatingFileHandler(
            Path.home() / self.config["LOGGING"]["ROBOT"], when="H", interval=1
        )
        handler.setFormatter(formatter)
        # handler.setLevel(logging.CRITICAL)
        self.logger.addHandler(handler)
        self.logger.propagate = False
        self.logcounter = 0

        self.logger.warning(f"Started a new robot: {now}")

    def tick(self, fishpos, fishdir, dists):
        try:
            # tick only if not controlled
            if not self.controlled or not self.user_controlled:
                super().tick(fishpos, fishdir, dists)

        except Exception as e:
            logging.error(f"ROBOT: Error in tick")
            logging.error(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(exc_type, fname, exc_tb.tb_lineno)

    def move(self):
        try:
            # change target if robot is controlled (joystick)
            if self.user_controlled or self.controlled:
                # print(f"ROBOT: new dir - {self.new_dir}")
                new_pos = self.pos + (self.new_dir * self.max_speed)
                # set next target in pixel coordinates
                self.target_px = self.pos + (self.new_dir * 200)

                # print(
                #   f"ROBOT: new px target: {self.target_px} check if outside of arena!!!!"
                # )

                # check if next target would be outside arena and update new_dir if its not
                inside = self.check_inside_arena(self.target_px)
                if not inside:
                    new_pos = self.pos + (self.new_dir * self.max_speed)
                    self.target_px = self.pos + (self.new_dir * 100)

                # check if near arena borders and repulse from nearest border point
                self.arena_points = self.arena.getNearestArenaPoints(new_pos)

                # if real robot don't go too close to wall
                if self.real_robot:
                    for idx, point in enumerate(self.arena_points):  # arena points
                        if point[1] < self.arena_repulsion:
                            logging.info(f"ROBOT: close point - {point[0]}")

                            if idx == 0:
                                self.new_dir = np.asarray([0.0, 1.0])  # go down
                            # right edge
                            elif idx == 1:
                                self.new_dir = np.asarray([-1.0, 0.0])  # go left
                            # bottom edge
                            elif idx == 2:
                                self.new_dir = np.asarray([0.0, -1.0])  # go up
                            # left edge
                            elif idx == 3:
                                self.new_dir = np.asarray([1.0, 0.0])  # go right

                            new_pos = self.pos + (self.new_dir * self.max_speed)
                            self.target_px = self.pos + (self.new_dir * 300)

                            # print(f"repulse from {point[0]}")

                self.pos = np.array(new_pos, dtype=np.float64)
                self.dir = self.new_dir
                self.dir_norm = normalize(self.dir)
                # new orientation is orientation of new direction vector
                self.ori = math.degrees(math.atan2(self.dir[1], self.dir[0]))

                # log direction every few ticks
                if self.logcounter == 5 and self.user_controlled:
                    self.logger.warning(f"{self.pos}, {self.dir}, {self.ori}")
                    self.logcounter = 0
                self.logcounter += 1

            # automatic movement if not in controlled state
            else:
                if self.real_robot is not None:
                    # new position is old position plus new direction vector times speed
                    new_pos = self.pos + (self.new_dir * self.max_speed)
                    # set next target in pixel coordinates
                    self.target_px = self.pos + (self.new_dir * 100)
                    # check if next target would be outside arena and update new_dir if its not
                    inside = self.check_inside_arena(self.target_px)
                    if not inside:
                        new_pos = self.pos + (self.new_dir * self.max_speed)
                        self.target_px = self.pos + (self.new_dir * 100)
                    self.pos = np.array(new_pos, dtype=np.float64)
                    self.dir = self.new_dir
                    self.dir_norm = normalize(self.dir)
                    # new orientation is orientation of new direction vector
                    self.ori = math.degrees(math.atan2(self.dir[1], self.dir[0]))

                # if no real robot just move automatically
                else:
                    super().move()

        except Exception as e:
            logging.error(f"\nROBOT: Error in move!")
            logging.error(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(exc_type, fname, exc_tb.tb_lineno)

    def check_inside_arena(self, next_pos) -> bool:
        # check if fish would go out of arena and correct direction if so
        next_pos_point = QPointF(next_pos[0], next_pos[1])
        arena_rect = self.arena.rect

        if not arena_rect.contains(next_pos_point):
            # print(f"Fish will outside of Arena!")
            # set pos to nearest arena wall (the one that was crossed)
            self.arena_points = np.asarray(self.arena_points, dtype=object)
            id_closest_arena_p = np.argmin(self.arena_points[:, 1])
            # self.pos = self.arena_points[id_closest_arena_p][0]
            # print(id_closest_arena_p)

            # set new dir toward the middle, away from wall
            # top edge
            if id_closest_arena_p == 0:
                self.new_dir = np.asarray([0.0, 1.0])  # go down
            # right edge
            elif id_closest_arena_p == 1:
                self.new_dir = np.asarray([-1.0, 0.0])  # go left
            # bottom edge
            elif id_closest_arena_p == 2:
                self.new_dir = np.asarray([0.0, -1.0])  # go up
            # left edge
            elif id_closest_arena_p == 3:
                self.new_dir = np.asarray([1.0, 0.0])  # go right
            return False
        return True
