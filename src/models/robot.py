from src.models.agent import Agent, normalize
import numpy as np
import math
from datetime import datetime
from collections import deque
from PyQt5.QtCore import *
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from src.util.util import Util
import os
import sys


class Robot(Agent):
    """
    Robot class.
    Inherits tick() and move() from agent class.
    Additionally handles automatic charging and user control.

    Args:
        Agent (Agent): Base Agent class
    """

    def __init__(self, arena, config):
        super().__init__(0, [1000, 1000], 90, arena, config)

        self.uid = 0
        self.util = Util(self.config)

        self.controlled = config["ROBOT"]["controlled_from_start"]
        self.debug = False
        self.voltage = 0.0
        self.old_voltage = None
        self.charging_history_length = self.config["ROBOT"]["charging_history_length"]
        self.old_voltages_minute_queue = deque(
            [], self.charging_history_length
        )  # one for each minute
        self.old_voltages_second_queue = deque([], 60)  # one for each second
        self.new_dir = np.asarray([0.00001, 0])
        self.real_robot = None
        self.target_px = [0, 0]
        self.charging = False
        self.go_to_charging_station = False
        self.full_charge = False
        self.user_controlled = False
        self.stop = False
        self.arena_repulsion = self.config["ROBOT"]["arena_repulsion"]

        self.min_voltage = self.config["ROBOT"]["min_voltage"]
        self.max_voltage = self.config["ROBOT"]["max_voltage"]

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

    def set_attributes(self, robot: dict):
        """
        Set robot attributes receives from RoboTracker

        Args:
            robot (dict): Tracked robot attributes
        """
        try:
            # charging
            self.set_charging(robot["chargingStatus"])
            self.set_voltage(robot["voltage"])

            self.uid = robot["uid"]

            # only update position when not charging
            if not self.charging:
                pos_cm = robot["position"]
                pos_px = self.util.map_cm_to_px(pos_cm)
                self.pos = np.asarray([pos_px[0], pos_px[1]])

                dir = robot["orientation"]
                inverted_dir = self.util.rotate_arena_to_world(dir)
                self.dir = np.asarray([inverted_dir[0], inverted_dir[1]])
                self.dir_norm = normalize(self.dir)
                self.ori = math.degrees(math.atan2(inverted_dir[1], inverted_dir[0]))

            # logging.info(
            #     f"ROBOT: voltage: {self.voltage}, pos: {pos_px}, charging status: {self.charging}"
            # )
        except Exception as e:
            logging.error(f"ROBOT: Error in attribute update")
            logging.error(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(exc_type, fname, exc_tb.tb_lineno)

    def tick(self, fishpos, fishdir, dists):
        """
        Calculate next direction using all other agents current positions, directions and distances

        Args:
            fishpos (list): All other fish positions
            fishdir (list): All other fish directions
            dists (_type_): Distance matrix of all agents
        """
        try:
            # tick only if not controlled
            if not self.controlled or not self.user_controlled:
                super().tick(fishpos, fishdir, dists)
            # dont tick if in charging state
            if self.charging or self.go_to_charging_station:
                return
        except Exception as e:
            logging.error(f"ROBOT: Error in tick")
            logging.error(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(exc_type, fname, exc_tb.tb_lineno)

    def move(self) -> None:
        """
        - Automated movement: Apply calculated directions from tick method
        - User controlled: Apply user controlled direction
        """
        try:
            # don't move elsewhere if charging or going to charging station
            # if self.charging or self.go_to_charging_station:
            #     return

            # change target if robot is controlled (joystick)
            if self.user_controlled or self.controlled:
                # print(f"ROBOT: new dir - {self.new_dir}")
                new_pos = self.pos + (self.new_dir * self.max_speed)
                # set next target in pixel coordinates
                self.target_px = self.pos + (self.new_dir * 200)

                # check if next target would be outside arena and update new_dir if its not
                inside = self.check_inside_arena(self.target_px)
                if not inside:
                    new_pos = self.pos + (self.new_dir * self.max_speed)
                    self.target_px = self.pos + (self.new_dir * 100)

                # check if near arena borders and repulse from nearest border point
                self.arena_points = self.arena.getNearestArenaPoints(new_pos)

                # if real robot don't go too close to wall
                if (
                    self.real_robot
                    and not self.charging
                    and not self.go_to_charging_station
                ):
                    for idx, point in enumerate(self.arena_points):  # arena points
                        if point[1] < self.arena_repulsion:
                            logging.info(f"ROBOT: close point - {point[0]}")
                            if not self.go_to_charging_station or self.charging:
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

            # automatic movement if not in charging or controlled state
            else:
                if (
                    self.real_robot is not None
                    and not self.charging
                    and not self.go_to_charging_station
                ):
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

    def set_voltage(self, voltage: float):
        """
        Set current voltage and check for charge status

        Args:
            voltage (float): Received voltage from RoboTracker
        """
        try:
            if voltage > 0:
                # first time voltage receive
                if self.old_voltage is None:
                    self.old_voltage = voltage
                    self.last_minute_volt_msg_time = datetime.now()
                    self.last_second_volt_msg_time = self.last_minute_volt_msg_time
                    self.old_voltages_minute_queue.append(voltage)
                    self.old_voltages_second_queue.append(voltage)
                else:
                    self.old_voltage = self.voltage

                # update voltage
                self.voltage = voltage

                # every minute add a voltage to the x min voltage list
                curr_time = datetime.now()
                time_delta = curr_time - self.last_minute_volt_msg_time
                # print(time_delta.total_seconds())
                delta_mins = np.floor(time_delta.total_seconds() / 60)
                # print(delta_mins)
                if delta_mins > 0:
                    self.old_voltages_minute_queue.append(self.voltage)
                    self.last_minute_volt_msg_time = curr_time

                # save voltage each second
                time_delta2 = curr_time - self.last_second_volt_msg_time
                delta_secs = np.floor(time_delta2.total_seconds())
                if delta_secs > 0:
                    self.old_voltages_second_queue.append(self.voltage)
                    self.last_second_volt_msg_time = curr_time

                # check if full by comparing voltage to voltage x minutes ago
                # set charging to false then
                self.check_if_full()

                # if voltage too low start charging routine in behavior
                self.check_if_low_charge()
        except Exception as e:
            logging.error("ROBOT: Error in set_voltage!")
            logging.error(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(exc_type, fname, exc_tb.tb_lineno)

    def set_charging(self, is_charging: bool):
        """
        Sets the charging status received from RoboTracker

        Args:
            is_charging (bool): Received charging status from RoboTracker
        """
        try:
            self.charging = is_charging

            if self.charging:
                self.go_to_charging_station = (
                    False  # arrived at charging station and is charging
                )
        except Exception as e:
            logging.error("ROBOT: Error in set_charging!")
            logging.error(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(exc_type, fname, exc_tb.tb_lineno)

    def check_if_full(self) -> None:
        """Check if fully charged"""
        # if voltage constant for x minutes
        voltage_list_min = list(self.old_voltages_minute_queue)
        voltage_list_sec = list(self.old_voltages_second_queue)

        # check if voltage x minutes ago the same as current or voltage larger than 8.5
        if (
            voltage_list_min[0] == self.voltage
            and len(voltage_list_min) == 10
            and self.voltage > self.config["ROBOT"]["mean_voltage_full"]
        ) or self.voltage > self.config["ROBOT"]["max_voltage"]:
            # logging.info("Robot is fully charged")
            self.full_charge = True

        # also check if mean gradient of voltage list is close to 0
        gradient = (
            np.gradient(voltage_list_min) if len(voltage_list_min) > 1 else 10
        )  # if not enough values: arbitrary high gradient value
        mean_grad = np.mean(gradient)
        mean_voltage = np.mean(voltage_list_min)
        if (
            math.isclose(mean_grad, 0, rel_tol=0.2)
            and mean_voltage > self.config["ROBOT"]["mean_voltage_full"]
        ):
            # print("Robot is fully charged (gradient)")
            self.full_charge = True

    def check_if_low_charge(self) -> None:
        """ """
        try:
            if self.voltage < self.min_voltage and not self.charging:
                logging.info("ROBOT: LOW CHARGE")
                self.go_to_charging_station = True
                self.full_charge = False
        except Exception as e:
            logging.error("ROBOT: Error in check_if_low_charge!")
            logging.error(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(exc_type, fname, exc_tb.tb_lineno)

    def set_robot(self, robot):
        """Set new robot

        Args:
            robot (dict): New robot attributes
        """
        try:
            self.real_robot = robot
            if robot:
                self.uid = robot["uid"]
                self.pos = np.asarray([robot["position"][0], robot["position"][1]])
                self.dir = np.asarray(
                    [robot["orientation"][0], robot["orientation"][1]]
                )
                self.ori = np.degrees(math.atan2(self.dir[1], self.dir[0]))

                logging.info(f"ROBOT: New robot set in pos: {self.pos}")
        except Exception as e:
            logging.error("ROBOT: Error in set_robot!")
            logging.error(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(exc_type, fname, exc_tb.tb_lineno)

    def check_inside_arena(self, next_pos) -> bool:
        """Check if position is inside arena and correct direction if not

        Args:
            next_pos (list): Position as [X,Y]

        Returns:
            bool: True: inside of arena; False: outside of arena 
        """
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
