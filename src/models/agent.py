import math, random
import numpy as np
from src.models.arena import Arena
from PyQt5.QtCore import *

class Agent():
    def __init__(self, id, pos, ori, arena, config, dir=None, zoa=None, zoo=None, zor=None, time_step=None):
        self.id = id
        self.pos = pos
        self.ori = ori
        self.dir = dir
        self.config = config

        if dir is None:
            rad_ori = np.radians(ori)
            self.dir =  np.asarray([math.cos(rad_ori), math.sin(rad_ori)]) / np.linalg.norm([math.cos(rad_ori), math.sin(rad_ori)])

        self.new_dir = None
        self.arena = arena
        self.time_step = time_step if time_step!=None else config["DEFAULTS"]["time_step"]

        self.error_rad = config['DEFAULTS']['error_rad']

        self.max_speed = config['DEFAULTS']['max_speed']
        self.max_turn_rate = config['DEFAULTS']['max_turn_rate'] # by second

        #zone radii
        self.zoa = zoa if zoa!=None else config["DEFAULTS"]["zoa"]
        self.zoo = zoo if zoo!=None else config["DEFAULTS"]["zoo"]
        self.zor = zor if zor!=None else config["DEFAULTS"]["zor"]
    
    def tick(self, fishpos, fishdir, dists):
        # time_start = time.perf_counter()
        pos = np.asarray(self.pos)
        old_rotation = self.ori
        # oldPos = self.pos

        theta = math.radians(old_rotation)
        self.dir = np.asarray([math.cos(theta), math.sin(theta)]) / np.linalg.norm([math.cos(theta), math.sin(theta)])
        dirt1 = self.dir

        # print(f"time before zone check: {time.perf_counter() - time_start}", flush=True)

        #get zone neighbors
        
        # use corresponding precalculated distmatrix row
        dists = np.asarray(dists)
        zor_iarr = (dists != 0) & (dists <= self.zor)
        zoo_iarr = (dists > self.zor) & (dists <= self.zoo)
        zoa_iarr = (dists > self.zoo) & (dists <= self.zoa)

        points_zor = fishpos[zor_iarr].tolist() # fish and arena points in zor
        points_zoo = fishdir[zoo_iarr].tolist() # fish in zoo
        points_zoa = fishpos[zoa_iarr].tolist() # fish in zoa

        # print(f"time before arena check: {time.perf_counter() - time_start}", flush=True)    
        arena_points = self.arena.getNearestArenaPoints(pos)
        for point in arena_points: #arena points
            if point[1] < self.config['ARENA']['repulsion']:
                points_zor.append(point[0])
        # print(f"time for zone check: {time.perf_counter() - time_start}", flush=True)

        # zone of repulsion (zor)
        n_zor = len(points_zor)
        if n_zor > 0:
            sum = np.asarray([.0,.0])
            for f in points_zor:
                # assert np.linalg.norm(np.asarray(f) - pos) != 0
                if np.any(np.asarray(f) - pos):
                    rij = (np.asarray(f) - pos) / np.linalg.norm(np.asarray(f) - pos)
                    urij = (rij/ np.linalg.norm(rij))
                    sum = sum + urij
            
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
        # print(f"time for zone apply: {time.perf_counter() - time_start}", flush=True)

        # add random noise rotation to new direction vector
        noise = math.radians(random.gauss(0,self.error_rad))
        # print(noise)
        rand_rot_matrix = np.array([[np.cos(noise), -np.sin(noise)], [np.sin(noise), np.cos(noise)]])
        dirt1 = np.dot(rand_rot_matrix, dirt1)

        #consider max turning rate theta
        len_dir = np.linalg.norm(self.dir)
        len_dirt1 = np.linalg.norm(dirt1)
        unit_vector_1 = (self.dir / len_dir) if len_dir != 0 else np.asarray([0,0])
        unit_vector_2 = (dirt1 / len_dirt1) if len_dirt1 != 0 else np.asarray([0,0])
        dot_product = np.dot(unit_vector_1, unit_vector_2)
        # curr_turn_angle = np.degrees(np.arccos(dot_product))

        # angle = math.atan2(unit_vector_2[1], unit_vector_2[0]) - math.atan2(unit_vector_1[1], unit_vector_1[0])
        # deg_angle = np.degrees(angle)

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

        #if dirt1 in not null it is new dir
        if len_dirt1 != 0:
            self.new_dir = dirt1/np.linalg.norm(dirt1)
        else: 
            self.new_dir = self.dir

        #check if fish would go out of arena and correct direction if so
        next_pos = self.pos + (self.new_dir * self.max_speed)
        next_pos_point = QPointF(next_pos[0], next_pos[1])
        arena_rect = self.arena.rect

        if not arena_rect.contains(next_pos_point):
            # print(f"Fish will outside of Arena!")
            #set pos to nearest arena wall (the one that was crossed)
            arena_points = np.asarray(arena_points)
            id_closest_arena_p = np.argmin(arena_points[:,1])
            # self.pos = arena_points[id_closest_arena_p][0]

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
        # print(f"time for fish tick: {time.perf_counter() - time_start}", flush=True)
    def move(self):
        # new position is old position plus new direction vector times speed
        new_pos = self.pos + (self.new_dir * self.max_speed)
        self.pos = new_pos
        self.dir = self.new_dir
        #new orientation is orientation of new direction vector
        self.ori = math.degrees(math.atan2(self.dir[1], self.dir[0]))

        # print(pos, self.pos)

    def check_inside_arena():
        pass