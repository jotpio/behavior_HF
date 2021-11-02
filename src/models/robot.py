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


class Robot(Agent):
    def __init__(self, arena, config):
        super().__init__(0, [1000, 1000], 90, arena, config)

        self.util = Util(self.config)

        self.controlled = config["ROBOT"]["controlled_from_start"]
        self.debug = False
        self.voltage = 0.0
        self.old_voltage = None
        self.max_charging_time = self.config["ROBOT"]["charging_time"]
        self.old_voltages_minute_queue = deque(
            [], self.max_charging_time
        )  # one for each minute
        self.old_voltages_second_queue = deque([], 60)  # one for each second
        self.new_dir = np.asarray([0.00001, 0])
        self.real_robot = None
        self.target_px = [0, 0]
        self.charging = False
        self.go_to_charging_station = False
        self.full_charge = False
        self.user_controlled = False
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

    def set_attributes(self, robot):
        pos_cm = robot.position
        pos_px = self.util.map_cm_to_px(pos_cm)
        self.pos = np.asarray([pos_px[0], pos_px[1]])

        dir = robot.orientation
        inverted_dir = self.util.rotate_arena_to_world(dir)
        self.dir = np.asarray([inverted_dir[0], inverted_dir[1]])
        self.dir_norm = normalize(self.dir)
        self.ori = math.degrees(math.atan2(inverted_dir[1], inverted_dir[0]))
        self.set_voltage(robot.voltage)
        self.set_charging(robot.chargingStatus)
        print(
            f"ROBOT: voltage: {self.voltage}, pos: {pos_px}, charging status: {self.charging}"
        )

    def tick(self, fishpos, fishdir, dists):
        try:
            # dont tick if in charging state
            if self.charging or self.go_to_charging_station:
                return
            # tick only if not controlled
            if not self.controlled or self.user_controlled:
                super().tick(fishpos, fishdir, dists)
        except:
            print(f"\nROBOT: Error in tick")

    def move(self):
        try:
            # don't move elsewhere if charging or going to charging station
            if self.charging or self.go_to_charging_station:
                return

            # change target if robot is controlled (joystick)
            if self.user_controlled or self.controlled:
                # print(f"ROBOT: new dir - {self.new_dir}")
                new_pos = self.pos + (self.new_dir * self.max_speed)
                # set next target in pixel coordinates
                self.target_px = self.pos + (self.new_dir * 100)

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

                for point in self.arena_points:  # arena points
                    if point[1] < self.arena_repulsion:
                        print(f"ROBOT: close point - {point[0]}")
                        # print(f"repulse from {point[0]}")

                self.pos = np.array(new_pos, dtype=np.float64)
                self.dir = self.new_dir
                self.dir_norm = normalize(self.dir)
                # new orientation is orientation of new direction vector
                self.ori = math.degrees(math.atan2(self.dir[1], self.dir[0]))

                # log direction every few ticks
                if self.logcounter == 5 and self.user_controlled:
                    self.logger.warning(f"{self.pos}, {self.dir}")
                    self.logcounter = 0
                self.logcounter += 1

            # automatic movement if not in charging or controlled state
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

        except:
            print(f"\nROBOT: Error in move!")

    def set_voltage(self, voltage):
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
        except:
            print("ROBOT: Error in set_voltage!")

    def set_charging(self, is_charging):
        try:
            self.charging = is_charging

            if self.charging:
                self.go_to_charging_station = (
                    False  # arrived at charging station and is charging
                )
        except:
            print("ROBOT: Error in set_charging!")

    def check_if_full(self):
        # if voltage constant for x minutes
        voltage_list_min = list(self.old_voltages_minute_queue)
        voltage_list_sec = list(self.old_voltages_second_queue)

        # print(f"ROBOT minute voltage list: {voltage_list_min}")
        # print(f"ROBOT second voltage list: {voltage_list_sec}")

        # check if voltage x minutes ago the same as current or voltage larger than 8.1
        if (
            voltage_list_min[0] == self.voltage
            and len(voltage_list_min) == 10
            and self.voltage > 7.8
        ) or self.voltage > 8.05:
            print("Robot is fully charged")
            self.full_charge = True

        # also check if mean gradient of voltage list is close to 0
        gradient = (
            np.gradient(voltage_list_min) if len(voltage_list_min) > 1 else 10
        )  # if not enough values: arbitrary high gradient value
        mean_grad = np.mean(gradient)
        mean_voltage = np.mean(voltage_list_min)
        if math.isclose(mean_grad, 0, rel_tol=0.2) and mean_voltage > 8:
            print("Robot is fully charged (gradient)")
        else:
            pass
            # print(f"Robot is NOT fully charged (gradient): {gradient}")

    def check_if_low_charge(self):
        try:
            if self.voltage < self.min_voltage and not self.charging:
                print("ROBOT: LOW CHARGE")
                self.go_to_charging_station = True
                self.full_charge = False
        except:
            print("ROBOT: Error in check_if_low_charge!")

    def set_robot(self, robot):
        try:

            self.real_robot = robot
            if robot:
                self.pos = np.asarray([robot.position[0], robot.position[1]])
                self.dir = np.asarray([robot.orientation[0], robot.orientation[1]])
                self.ori = np.degrees(math.atan2(self.dir[1], self.dir[0]))

                print(f"Behavior - Robot: {self.pos}")
        except:
            print("ROBOT: Error in set_robot!")

    def check_inside_arena(self, next_pos):
        # check if fish would go out of arena and correct direction if so
        next_pos_point = QPointF(next_pos[0], next_pos[1])
        arena_rect = self.arena.rect

        if not arena_rect.contains(next_pos_point):
            # print(f"Fish will outside of Arena!")
            # set pos to nearest arena wall (the one that was crossed)
            self.arena_points = np.asarray(self.arena_points, dtype=object)
            id_closest_arena_p = np.argmin(self.arena_points[:, 1])
            # self.pos = self.arena_points[id_closest_arena_p][0]
            print(id_closest_arena_p)

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
