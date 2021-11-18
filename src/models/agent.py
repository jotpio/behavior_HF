from logging import exception
import math
import random
import time
import logging
import os, sys

import numpy as np
from numba import jit
from PyQt5.QtCore import *
from src.models.arena import Arena


class Agent:
    def __init__(
        self,
        id,
        pos,
        ori,
        arena,
        config,
        dir=None,
        zor=None,
        zoo=None,
        zoa=None,
        time_step=None,
    ):
        self.id = id
        self.pos = np.array(pos, dtype=np.float64)
        self.ori = ori
        self.dir = dir
        self.config = config
        self.influenced_by_robot = False
        self.repulsed = False
        self.optimisation_individual = config["DEBUG"]["optimisation_individual"]

        if dir is None:
            rad_ori = np.radians(ori)
            self.dir = np.asarray(
                [math.cos(rad_ori), math.sin(rad_ori)]
            ) / np.linalg.norm([math.cos(rad_ori), math.sin(rad_ori)])

        self.dir_norm = self.dir / np.linalg.norm(self.dir)
        self.new_dir = np.asarray([0.1, 0])
        self.arena = arena
        self.arena_points = None
        self.time_step = (
            time_step if time_step != None else config["DEFAULTS"]["time_step"]
        )

        self.error_deg = config["DEFAULTS"]["error_deg"]

        self.max_speed = config["DEFAULTS"]["max_speed"]
        self.max_turn_rate = config["DEFAULTS"]["max_turn_rate"]  # by second

        # zone radii
        self.zor = zor if zor != None else config["DEFAULTS"]["zor"]
        self.zoo = zoo if zoo != None else config["DEFAULTS"]["zoo"]
        self.zoa = zoa if zoa != None else config["DEFAULTS"]["zoa"]

        self.vision_angle = config["DEFAULTS"]["vision_angle"]
        self.half_vision_cos = np.cos(np.radians(self.vision_angle / 2))

    def tick(self, fishpos, fishdir, dists):
        try:
            #
            # preparations
            #
            if self.optimisation_individual:
                time_start = time.perf_counter()
            pos = np.asarray(self.pos)
            old_rotation = self.ori
            arena_repulsion = self.config["ARENA"]["repulsion"]

            theta = math.radians(old_rotation)
            self.dir = np.asarray([math.cos(theta), math.sin(theta)]) / np.linalg.norm(
                [math.cos(theta), math.sin(theta)]
            )
            dirt1 = self.dir
            if self.optimisation_individual:
                t1 = time.perf_counter()
                print(f"time before zone check: {t1 - time_start}", flush=True)

            #
            # get zone neighbors
            #
            try:
                # use corresponding precalculated distmatrix row
                (
                    points_zor,
                    dirs_zoo,
                    points_zoa,
                    self.influenced_by_robot,
                ) = get_zone_neighbours(
                    dists, fishpos, fishdir, self.zor, self.zoo, self.zoa
                )
                points_zor = points_zor.tolist()

                if self.optimisation_individual:
                    t2 = time.perf_counter()
                    print(f"time for zone check: {t2 - t1}", flush=True)
            except Exception as e:
                logging.error(f"\nAGENT: Error in zone neighbor check - id {self.id}")
                logging.error(e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                logging.error(exc_type, fname, exc_tb.tb_lineno)

            try:
                # check if near arena borders and repulse from nearest border point
                self.arena_points = self.arena.getNearestArenaPoints(pos)

                for point in self.arena_points:  # arena points
                    if point[1] < arena_repulsion:
                        points_zor.append(point[0])
                        # print(f"repulse from {point[0]}")
                points_zor = np.asarray(points_zor)
                if self.optimisation_individual:
                    t3 = time.perf_counter()
                    print(f"time for arena check: {t3 - t2}", flush=True)
            except Exception as e:
                logging.error(f"\nAGENT: Error in arena point check - id {self.id}")
                logging.error(e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                logging.error(exc_type, fname, exc_tb.tb_lineno)
            #
            # for each point in radii check if in vision
            #
            try:
                points_zor, dirs_zoo, points_zoa = check_in_radii_vision(
                    points_zor,
                    dirs_zoo,
                    points_zoa,
                    self.half_vision_cos,
                    self.dir_norm,
                    np.asarray(self.pos),
                )
                if self.optimisation_individual:
                    t4 = time.perf_counter()
                    print(f"time for vision check: {t4 - t3}", flush=True)
            except Exception as e:
                logging.error(f"\nAGENT: Error in radii check - id {self.id}")
                logging.error(e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                logging.error(exc_type, fname, exc_tb.tb_lineno)

            #
            # zone calculations
            #

            # zone of repulsion (zor)
            n_zor = len(points_zor)
            if n_zor > 0:
                try:
                    # repulse
                    dirt1 = repulse(np.asarray(points_zor), pos)
                    self.repulsed = True
                except Exception as e:
                    logging.error(f"\nAGENT: Error in repulsion - id {self.id}")
                    logging.error(e)
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    logging.error(exc_type, fname, exc_tb.tb_lineno)
                # print("repulse")
            # if no fish or wall in zone of repulsion
            else:
                # print("no repulse")
                n_zoo = len(dirs_zoo)
                n_zoa = len(points_zoa)

                self.repulsed = False

                dir_o = np.asarray([0, 0])
                if n_zoo > 0:
                    try:
                        # align
                        dir_o = align(np.asarray(dirs_zoo))
                    except Exception as e:
                        logging.error(f"\nAGENT: Error in align - id {self.id}")
                        logging.error(e)
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                        logging.error(exc_type, fname, exc_tb.tb_lineno)

                dir_a = np.asarray([0, 0])
                if n_zoa > 0:
                    try:
                        # attract
                        dir_a = attract(np.asarray(points_zoa), pos)
                    except Exception as e:
                        logging.error(f"\nAGENT: Error in attract - id {self.id}")
                        logging.error(e)
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                        logging.error(exc_type, fname, exc_tb.tb_lineno)

                # combine calculated directions
                if n_zoa == 0 and n_zoo > 0:
                    dirt1 = dir_o
                elif n_zoo == 0 and n_zoa > 0:
                    dirt1 = dir_a
                elif n_zoo > 0 and n_zoa > 0:
                    dirt1 = np.mean([dir_a, dir_o], axis=0)

            if self.optimisation_individual:
                t5 = time.perf_counter()
                print(f"time for zone apply: {t5 - t4}", flush=True)

            #
            # add random noise rotation to new direction vector
            #
            try:
                noise = math.radians(random.gauss(0, self.error_deg))
                # print(noise)
                rand_rot_matrix = np.array(
                    [[np.cos(noise), -np.sin(noise)], [np.sin(noise), np.cos(noise)]]
                )
                dirt1 = np.dot(rand_rot_matrix, dirt1)
            except Exception as e:
                logging.error(f"\nAGENT: Error in rotation noise - id {self.id}")
                logging.error(e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                logging.error(exc_type, fname, exc_tb.tb_lineno)

            #
            # consider max turning rate theta
            #
            try:
                len_dir = np.linalg.norm(self.dir)
                len_dirt1 = np.linalg.norm(dirt1)
                unit_vector_1 = (
                    (self.dir / len_dir) if len_dir != 0 else np.asarray([0.0, 0.0])
                )
                unit_vector_2 = (
                    (dirt1 / len_dirt1) if len_dirt1 != 0 else np.asarray([0.0, 0.0])
                )
                dot_product = np.dot(unit_vector_1, unit_vector_2)

                det = np.linalg.det([unit_vector_1, unit_vector_2])
                deg_angle2 = np.degrees(math.atan2(det, dot_product))

                curr_turn_angle = deg_angle2
                #
                # clip direction to move only by max turn rate
                #
                if np.abs(curr_turn_angle) > self.max_turn_rate * self.time_step:

                    clipped_turn_angle = np.radians(
                        np.sign(curr_turn_angle) * self.max_turn_rate * self.time_step
                    )
                    clipped_rot_matrix = np.array(
                        [
                            [np.cos(clipped_turn_angle), -np.sin(clipped_turn_angle)],
                            [np.sin(clipped_turn_angle), np.cos(clipped_turn_angle)],
                        ]
                    )
                    dirt1 = np.dot(
                        clipped_rot_matrix, self.dir
                    )  # rotate only by clipped rotation angle toward new direction
            except Exception as e:
                logging.error(f"\nAGENT: Error in rotation clipping - id {self.id}")
                logging.error(e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                logging.error(exc_type, fname, exc_tb.tb_lineno)
            # if dirt1 in not null it is new dir
            if len_dirt1:
                self.new_dir = normalize(np.asarray(dirt1))
            else:
                self.new_dir = self.dir

            if self.optimisation_individual:
                t6 = time.perf_counter()
                print(f"time for turn check and random noise: {t6 - t5} \n", flush=True)
            if self.optimisation_individual:
                t7 = time.perf_counter()
                print(f"time for fish tick: {t7 - time_start} \n", flush=True)
        except Exception as e:
            logging.error(f"\nAGENT: Error in tick - id {self.id}")
            logging.error(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(exc_type, fname, exc_tb.tb_lineno)

    def move(self):
        try:
            # new position is old position plus new direction vector times speed
            new_pos = self.pos + (self.new_dir * self.max_speed)
            # check if next position would be outside arena and update new_dir if its not
            inside = self.check_inside_arena(new_pos)
            if not inside:
                new_pos = self.pos + (self.new_dir * self.max_speed)
            self.pos = np.array(new_pos, dtype=np.float64)
            self.dir = self.new_dir
            self.dir_norm = normalize(self.dir)
            # new orientation is orientation of new direction vector
            self.ori = math.degrees(math.atan2(self.dir[1], self.dir[0]))
        except Exception as e:
            logging.error(f"\nAGENT: Error in move - id {self.id}")
            logging.error(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(exc_type, fname, exc_tb.tb_lineno)

        # print(pos, self.pos)

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
            # print(id_closest_arena_p)
            # set new dir parallel to closest arena wall

            # top edge
            if id_closest_arena_p == 0:
                if self.new_dir[0] < 0 and self.new_dir[1] < 0:
                    self.new_dir = np.asarray([-1.0, 0.0])  # go left
                elif self.new_dir[0] >= 0 and self.new_dir[1] < 0:
                    self.new_dir = np.asarray([1.0, 0.0])  # go right
            # right edge
            elif id_closest_arena_p == 1:
                if self.new_dir[0] > 0 and self.new_dir[1] < 0:
                    self.new_dir = np.asarray([0.0, -1.0])  # go up
                elif self.new_dir[0] > 0 and self.new_dir[1] >= 0:
                    self.new_dir = np.asarray([0.0, 1.0])  # go down
            # bottom edge
            elif id_closest_arena_p == 2:
                if self.new_dir[0] > 0 and self.new_dir[1] > 0:
                    self.new_dir = np.asarray([1.0, 0.0])  # go right
                elif self.new_dir[0] <= 0 and self.new_dir[1] > 0:
                    self.new_dir = np.asarray([-1.0, 0.0])  # go left
            # left edge
            elif id_closest_arena_p == 3:
                if self.new_dir[0] < 0 and self.new_dir[1] > 0:
                    self.new_dir = np.asarray([0.0, 1.0])  # go down
                elif self.new_dir[0] < 0 and self.new_dir[1] <= 0:
                    self.new_dir = np.asarray([0.0, -1.0])  # go up
            return False

    def change_zones(self, zor=None, zoo=None, zoa=None):
        if zor:
            self.zor = zor
        if zoo:
            self.zoo = zoo
        if zoa:
            self.zoa = zoa


@jit(nopython=True)
def check_in_vision(half_vision_cos, dir_norm, pos, point):
    between_v = np.asarray(point) - pos
    between_v_norm = between_v / np.linalg.norm(between_v.astype(np.float64))
    dot = np.dot(between_v_norm, dir_norm)
    # deg_angle = np.degrees(np.arccos(dot))
    # print(deg_angle)
    if dot <= half_vision_cos:
        # print(f"not in vision - dot {dot}")
        return False
    # else:
    #     print(f"in vision - dot {dot}")
    # if deg_angle > 300 / 2:
    #     print(f"not in vision - angle {deg_angle}")

    #     if dot < 300:
    #         # print("not dot")
    #         pass
    #     else:
    #         # print("dot")
    #         pass
    #     return False
    # print(f"in vision - angle {deg_angle}")
    return True


@jit(nopython=True)
def check_in_radii_vision(p_zor, d_zoo, p_zoa, half_vision_cos, dir_norm, pos):
    points_zor = []
    for p in p_zor:
        if check_in_vision(half_vision_cos, dir_norm, pos, np.asarray(p)):
            points_zor.append(p)

    # skip if any repulsion
    dirs_zoo, points_zoa = (
        [np.array([np.float64(i), np.float64(i)]) for i in range(0)],
        [np.array([np.float64(i), np.float64(i)]) for i in range(0)],
    )
    if len(points_zor) == 0:
        for p in d_zoo:
            if check_in_vision(half_vision_cos, dir_norm, pos, np.asarray(p)):
                dirs_zoo.append(p)

        for p in p_zoa:
            if check_in_vision(half_vision_cos, dir_norm, pos, np.asarray(p)):
                points_zoa.append(p)

    return points_zor, dirs_zoo, points_zoa


@jit(nopython=True)
def get_zone_neighbours(dists, fishpos, fishdir, zor, zoo, zoa):
    zor_iarr = (dists != 0) & (dists <= zor)
    zoo_iarr = (dists > zor) & (dists <= zoo)
    zoa_iarr = (dists > zoo) & (dists <= zoa)

    # check if robot (id = 0) in attraction zone
    if zoa_iarr[0] or zoo_iarr[0]:
        influenced_by_robot = True
    else:
        influenced_by_robot = False
    points_zor = fishpos[zor_iarr]  # fish and arena points in zor
    dirs_zoo = fishdir[zoo_iarr]  # fish in zoo
    points_zoa = fishpos[zoa_iarr]  # fish in zoa

    return points_zor, dirs_zoo, points_zoa, influenced_by_robot


@jit(nopython=True)
def repulse(points_zor, pos):
    sum = np.asarray([0.0, 0.0])
    for f in points_zor:
        # assert np.linalg.norm(np.asarray(f) - pos) != 0
        if np.any(f - pos):
            rij = (f - pos) / np.linalg.norm(f - pos)
            urij = rij / np.linalg.norm(rij)
            sum = sum + urij

    dir_r = -sum

    return dir_r


@jit(nopython=True)
def align(dirs_zoo):
    # dir_o = np.asarray([0.0, 0.0])
    # for dir in dirs_zoo:
    #     dir_o = dir_o + (np.asarray(dir) / np.linalg.norm(np.asarray(dir)))
    unit_dirs_zoo = normalize(dirs_zoo)
    # print(unit_dirs_zoo)
    return np.sum(unit_dirs_zoo, axis=0)


@jit(nopython=True)
def attract(points_zoa, pos):
    dirs_tw_neighbors = (
        points_zoa - pos
    )  # array of directions towards neighbors in range
    unit_dirs_tw_neighbors = normalize(dirs_tw_neighbors)

    return np.sum(unit_dirs_tw_neighbors, axis=0)
    # unit_pos_zoa = normalize(points_zoa)
    # for f in points_zoa:
    #     dir_a = dir_a + ((np.asarray(f) - pos) / np.linalg.norm(np.asarray(f) - pos))


@jit(nopython=True)
def normalize(v):
    """
    Normalize vectors or arrays of vectors (matrices)

    input vector must be a ndarray!
    vector magnitude cannot be 0!
    from: https://stackoverflow.com/questions/2850743/numpy-how-to-quickly-normalize-many-vectors
    """
    magnitudes = np.sqrt((v ** 2).sum(-1))
    if v.ndim > 1:
        magnitudes = np.expand_dims(magnitudes, 1)
    # check if magnitudes nan or 0
    if np.any(np.asarray(np.isnan(magnitudes))) or np.all(np.asarray(magnitudes == 0)):
        out = v
    else:
        out = v / magnitudes
    return out
