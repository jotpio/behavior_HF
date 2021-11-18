import numpy as np
import logging, os, sys

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
        except Exception as e:
            logging.error(f"UTIL: Error in mapping cm to px")
            logging.error(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(exc_type, fname, exc_tb.tb_lineno)

    # mapping only works with a square arena and world
    def map_px_to_cm(self, v):
        try:
            inverted_v = [self.arena_w - v[0], self.arena_h - v[1]]
            return np.asarray(inverted_v) * self.arena_to_world_ratio
        except Exception as e:
            logging.error(f"UTIL: Error in mapping px to cm")
            logging.error(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(exc_type, fname, exc_tb.tb_lineno)

    def rotate_arena_to_world(self, v):
        return np.asarray([-v[0], -v[1]])
