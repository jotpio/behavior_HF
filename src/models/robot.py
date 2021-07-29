from src.models.agent import Agent

class Robot(Agent):
    def __init__(self, arena, config):
        super().__init__(-1, [100,100], 90, arena, config)

        self.controlled = False
        self.battery = 100
    
    def tick(self, fishpos, fishdir, dists):
        if not self.controlled:
            super().tick(fishpos, fishdir, dists)
    
    def move(self):
        if not self.controlled:
            super().move()
        else: 
            super().move()