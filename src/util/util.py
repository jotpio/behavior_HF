import numpy as np
import logging

FORMAT = "\t%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


class Util:
    def __init__(self, config):

        self.config = config
        self.world_w = self.config["WORLD"]["width"]
        self.world_h = self.config["WORLD"]["height"]
        self.arena_w = self.config["ARENA"]["width"]
        self.arena_h = self.config["ARENA"]["height"]

        self.arena_to_world_ratio = self.world_w / self.arena_w
        self.world_to_arena_ratio = self.arena_w / self.world_w

        # self.cm_to_px_mapper = interp1d([0,self.world_w],[0,self.arena_w])
        # self.px_to_cm_mapper = interp1d([0,self.arena_w],[0,self.world_w])

    # mapping only works with a square arena and world
    def map_cm_to_px(self, v):
        try:
            pixel_v = np.asarray(v) * self.world_to_arena_ratio
            return np.asarray([self.arena_w - pixel_v[0], self.arena_h - pixel_v[1]])
        except:
            logging.error(f"UTIL: Error in mapping cm to px")
        # try:
        #     return self.cm_to_px_mapper(v)
        # except:
        #     print(f"Error in cm to px mapping: {v}")
        #     return v

    # mapping only works with a square arena and world
    def map_px_to_cm(self, v):
        try:
            inverted_v = [self.arena_w - v[0], self.arena_h - v[1]]
            return np.asarray(inverted_v) * self.arena_to_world_ratio
        except:
            logging.error(f"UTIL: Error in mapping px to cm")

        # try:
        #     return self.px_to_cm_mapper(v)
        # except:
        #     print(f"Error in px to cm mapping: {v}")
        #     return v

    def rotate_arena_to_world(self, v):
        return np.asarray([-v[0], -v[1]])
