import numpy as np
from src.models.fish import Fish
from src.models.robot import Robot

def serialize(robot, allfish):
    out = []
    # robot
    # out.append([np.rint(self.behavior_robot.pos).tolist(), np.around(self.behavior_robot.ori, decimals=2), self.behavior_robot.id])
    robo_dict = {
        "id": robot.id,
        "orientation": np.around(robot.ori, decimals=2),
        "position": np.rint(robot.pos).tolist(),
    }
    out.append(robo_dict)
    # fish
    for a in allfish:
        fish_dict = {
            "id": a.id,
            "orientation": np.around(a.ori, decimals=2),
            "position": np.rint(a.pos).tolist(),
            "following": a.following,
            "repulsed": a.repulsed,
        }
        # out.append([np.rint(a.pos).tolist(), np.around(a.ori, decimals=2), a.id])
        out.append(fish_dict)

    return out