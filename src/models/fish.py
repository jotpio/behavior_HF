import math, random
import numpy as np
from src.models.arena import Arena
from src.models.agent import Agent
from PyQt5.QtCore import *


class Fish():
    def __init__(self, id, pos, ori, dir, arena, zoa, zoo, zor, time_step):
        self.id = id
        self.pos = pos
        self.ori = ori
        self.dir = dir

        if dir == []:
            rad_ori = np.radians(ori)
            self.dir =  np.asarray([math.cos(rad_ori), math.sin(rad_ori)]) / np.linalg.norm([math.cos(rad_ori), math.sin(rad_ori)])

        self.new_dir = None
        self.arena = arena
        self.time_step = time_step

        self.error_rad = 10

        self.max_speed = 10
        self.max_turn_rate = 100 # by second

        #zone radii
        self.zoa = zoa
        self.zoo = zoo
        self.zor = zor
    
    def tick(self, fishpos):
        pos = np.asarray(self.pos)
        old_rotation = self.ori
        # oldPos = self.pos

        theta = math.radians(old_rotation)
        self.dir = np.asarray([math.cos(theta), math.sin(theta)]) / np.linalg.norm([math.cos(theta), math.sin(theta)])

        dirt1 = self.dir

        #get zone neighbors
        points_zor = [] # fish and arena points in zor
        points_zoo = [] # fish in zoo
        points_zoa = [] # fish in zoa
        for f in fishpos: # fish
            if f.id != self.id:
                dist_to_point = np.linalg.norm(pos - f.pos)
                if dist_to_point < self.zor:
                    points_zor.append(f.pos)
                elif dist_to_point > self.zor and dist_to_point < self.zoo:
                    points_zoo.append(f.dir)
                elif dist_to_point > self.zoo and dist_to_point < self.zoa:
                    points_zoa.append(f.pos)
                
        arena_points = self.arena.getNearestArenaPoints(pos)
        for point in arena_points: #arena points
            if point[1] < 150:
                points_zor.append(point[0])

        # zone of repulsion (zor)
        n_zor = len(points_zor)
        if n_zor > 0:
            sum = [0,0]
            for f in points_zor:
                rij = (np.asarray(f) - pos) / np.linalg.norm(np.asarray(f) - pos)
                sum += rij/ np.linalg.norm(rij)
            
            dir_r = -sum
            
            dirt1 = dir_r
            # print(f"{self.id} repulsed!")

        # if no fish or wall in zone of repulsion
        else:
            n_zoo = len(points_zoo)
            n_zoa = len(points_zoa)

            dir_o = np.asarray([0,0])
            if n_zoo > 0:
                for dir in points_zoo:
                    dir_o = dir_o + (np.asarray(dir)/np.linalg.norm(np.asarray(dir)))
            
            dir_a = np.asarray([0,0])
            if n_zoa > 0:
                for f in points_zoa:
                    dir_a = dir_a + ((np.asarray(f) - pos)/np.linalg.norm(np.asarray(f) - pos))

            if n_zoa == 0 and n_zoo > 0:
                dirt1 = dir_o
                # print(f"{self.id} only alligned!")
            elif n_zoo == 0 and n_zoa > 0:
                dirt1 = dir_a
                # print(f"{self.id} only attracted!")
            elif n_zoo > 0 and n_zoa > 0:
                dirt1 = np.mean([dir_a, dir_o], axis = 0)
                # print(f"{self.id} attracted and alligned!")

        # add random noise rotation to new direction vector
        noise = math.radians(random.gauss(0,self.error_rad))
        # print(noise)
        rand_rot_matrix = np.array([[np.cos(noise), -np.sin(noise)], [np.sin(noise), np.cos(noise)]])
        dirt1 = np.dot(rand_rot_matrix, dirt1)

        #consider max turning rate theta
        unit_vector_1 = self.dir / np. linalg.norm(self.dir)
        unit_vector_2 = dirt1 / np. linalg.norm(dirt1)
        dot_product = np.dot(unit_vector_1, unit_vector_2)
        # curr_turn_angle = np.degrees(np.arccos(dot_product))

        angle = math.atan2(unit_vector_2[1], unit_vector_2[0]) - math.atan2(unit_vector_1[1], unit_vector_1[0])
        deg_angle = np.degrees(angle)

        det = np.linalg.det([unit_vector_1, unit_vector_2])
        deg_angle2 = np.degrees(math.atan2(det, dot_product))

        # np.testing.assert_almost_equal(np.abs(deg_angle), np.abs(deg_angle2))
        # if(not math.isclose(deg_angle, deg_angle2)):
            # print(deg_angle, deg_angle2)

        curr_turn_angle = deg_angle2

        #clip direction to move only by max turn rate
        if np.abs(curr_turn_angle) > self.max_turn_rate*self.time_step:
            clipped_turn_angle = np.radians(np.sign(curr_turn_angle) * self.max_turn_rate*self.time_step)
            clipped_rot_matrix = np.array([[np.cos(clipped_turn_angle), -np.sin(clipped_turn_angle)], [np.sin(clipped_turn_angle), np.cos(clipped_turn_angle)]])
            dirt1 = np.dot(clipped_rot_matrix, self.dir) #rotate only by clipped rotation angle toward new direction

        self.new_dir = dirt1/np.linalg.norm(dirt1)

        #check if fish would go out of arena and correct direction if so
        next_pos = self.pos + (self.new_dir * self.max_speed)
        next_pos_point = QPointF(next_pos[0], next_pos[1])
        arena_rect = self.arena.rect

        if not arena_rect.contains(next_pos_point):
            # print(f"Fish will outside of Arena!")
            #set pos to nearest arena wall (the one that was crossed)
            arena_points = np.asarray(arena_points)
            id_closest_arena_p = np.argmin(arena_points[:,1])

            #set new dir parallel to closest arena wall

            #top edge
            if id_closest_arena_p == 0 :
                if self.new_dir[0] < 0 and self.new_dir[1] < 0:
                    self.new_dir = np.asarray([-1,0]) #go left
                elif self.new_dir[0] >= 0 and self.new_dir[1] < 0:
                    self.new_dir = np.asarray([1,0]) #go right
            #right edge
            elif id_closest_arena_p == 1 :
                if self.new_dir[0] > 0 and self.new_dir[1] < 0:
                    self.new_dir = np.asarray([0,-1]) #go up
                elif self.new_dir[0] > 0 and self.new_dir[1] >= 0:
                    self.new_dir = np.asarray([0,1]) #go down
            #bottom edge
            elif id_closest_arena_p == 2 :
                if self.new_dir[0] > 0 and self.new_dir[1] > 0:
                    self.new_dir = np.asarray([1,0]) #go right
                elif self.new_dir[0] <= 0 and self.new_dir[1] > 0:
                    self.new_dir = np.asarray([-1,0]) #go left
            #left edge
            elif id_closest_arena_p == 3 :
                if self.new_dir[0] < 0 and self.new_dir[1] > 0:
                    self.new_dir = np.asarray([0,1]) #go down
                elif self.new_dir[0] < 0 and self.new_dir[1] <= 0:
                    self.new_dir = np.asarray([0,-1]) #go up

    def move(self):
        # new position is old position plus new direction vector times speed
        new_pos = self.pos + self.new_dir * self.max_speed
        self.pos = new_pos
        self.dir = self.new_dir
        #new orientation is orientation of new direction vector
        self.ori = math.degrees(math.atan2(self.dir[1], self.dir[0]))

        # print(pos, self.pos)