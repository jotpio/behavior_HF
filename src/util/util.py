from scipy.interpolate import interp1d

class Util:
    def __init__(self, config):

        self.config = config
        self.world_w = self.config["WORLD"]["width"]
        self.world_h = self.config["WORLD"]["height"]
        self.arena_w = self.config["ARENA"]["width"]
        self.arena_h = self.config["ARENA"]["height"]

        self.cm_to_px_mapper = interp1d([0,self.world_w],[0,self.arena_w])
        self.px_to_cm_mapper = interp1d([0,self.arena_w],[0,self.world_w]) 

    # mapping only works with a square arena and world
    def map_cm_to_px(self, v):
        return self.cm_to_px_mapper(v)
    

    # mapping only works with a square arena and world
    def map_px_to_cm(self, v):
        return self.px_to_cm_mapper(v)