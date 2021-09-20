from src.models.agent import Agent, normalize
import numpy as np
import math
import time
from  datetime import datetime
from collections import deque

class Robot(Agent):
    def __init__(self, arena, config):
        super().__init__(0, [100, 100], 90, arena, config)

        self.controlled = config["ROBOT"]["controlled_from_start"]
        self.debug = False
        self.voltage = 0
        self.old_voltage = None
        self.max_charging_time = self.config["ROBOT"]["charging_time"]
        self.old_voltages_minute_queue = deque([0,0,0,0,0,0,0,0,0,0], self.max_charging_time) # one for each minute
        self.new_dir = np.asarray([0.1, 0])
        self.real_robot = None
        self.target_px = [0, 0]
        self.auto_move = False
        self.charging = False
        self.at_charging_port = False
        self.go_to_charging_station = False

        self.min_voltage = self.config["ROBOT"]["min_voltage"]
        self.max_voltage = self.config["ROBOT"]["max_voltage"]

    def tick(self, fishpos, fishdir, dists):
        if self.charging:
            return

        if self.debug or not self.auto_move:
            return
        if not self.controlled:
            super().tick(fishpos, fishdir, dists)

    def move(self):
        if self.charging:
            return

        if self.controlled:
            # print(f"ROBOT: new dir - {self.new_dir}")
            new_pos = self.pos + (self.new_dir * self.max_speed)

            self.target_px = self.pos + (self.new_dir * 100)
            self.pos = np.array(new_pos, dtype=np.float64)
            self.dir = self.new_dir
            self.dir_norm = normalize(self.dir)
            # new orientation is orientation of new direction vector
            self.ori = math.degrees(math.atan2(self.dir[1], self.dir[0]))

        elif self.auto_move:
            if self.real_robot is not None:
                # new position is old position plus new direction vector times speed
                new_pos = self.pos + (self.new_dir * self.max_speed)
                # check if next position would be outside arena and update new_dir if its not
                inside = self.check_inside_arena(new_pos)
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
        else:
            print(f"ROBOT: No Movement")

    def set_voltage(self, voltage):
        # first time voltage receive
        if self.old_voltage is None:
            self.old_voltage = voltage
            self.last_minute_volt_msg_time = datetime.now()
            self.old_voltages_minute_queue.append(voltage)
        else:
            self.old_voltage = self.voltage

        #update voltage
        self.voltage = voltage

        #every minute add a voltage to the x min voltage list
        curr_time = datetime.now()
        time_delta = self.last_minute_volt_msg_time - curr_time
        delta_mins = np.floor(time_delta.total_seconds()/60)
        if delta_mins > 0:
            self.old_voltages_minute_queue.append(self.voltage)
            self.last_minute_volt_msg_time = curr_time
        
        #first check if charging
        self.check_if_charging()

        #check if full by comparing voltage to voltage x minutes ago
        #set charging to false then
        self.check_if_full()

        # if voltage too low start charging routine
        if self.voltage < self.min_voltage and not self.charging:
            self.go_to_charging_station = True

    def check_if_charging(self):
        if self.voltage and self.old_voltage:
            # check for voltage jump -> it may be charging
            if self.voltage > self.old_voltage:
                print("it may be charging")
                self.charging = True
                self.at_charging_port = True

    def check_if_full(self):
        #if voltage constant at max_voltage for x minutes
        voltage_list = list(self.old_voltages_minute_queue)
        
        # check if voltage x minutes ago the same as current
        if voltage_list[0] == self.voltage:
            print("Robot is fully charged")
            self.charging = False

    def set_robot(self, robot):
        self.real_robot = robot
        if robot:
            self.pos = np.asarray([robot.position[0], robot.position[1]])
            self.dir = np.asarray([robot.orientation[0], robot.orientation[1]])
            self.ori = np.degrees(math.atan2(self.dir[1], self.dir[0]))

            print(f"Behavior - Robot: {self.pos}")
