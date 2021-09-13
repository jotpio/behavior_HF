from src.models.agent import Agent, normalize
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
        self.target_px = [0,0]
        self.auto_move = False

    def tick(self, fishpos, fishdir, dists):
        if self.debug or not self.auto_move:
            return
        if not self.controlled:
            super().tick(fishpos, fishdir, dists)

    def move(self):
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
