from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import numpy as np


class Arena:
    """Arena class.
    This class is used to check for distances to the arena walls
    """

    def __init__(self, anchor_point, width, height):
        self.anchor_point = anchor_point
        self.width = width
        self.height = height
        self.rect = QRectF(anchor_point[0], anchor_point[1], width, height)
        self.rectItem = QGraphicsRectItem(self.rect)

    def getRectItem(self):
        return self.rectItem

    # get nearest point on rect to point and distance to it
    def getNearestArenaPoints(self, point):
        ax = self.anchor_point[0]
        ay = self.anchor_point[1]

        p = np.asarray(point)

        # closest points on four edges
        cl1 = np.asarray([p[0], ay])
        cl2 = np.asarray([ax + self.width, p[1]])
        cl3 = np.asarray([p[0], ay + self.height])
        cl4 = np.asarray([ax, p[1]])

        # distance to closest points
        d1 = np.linalg.norm(p - cl1)
        d2 = np.linalg.norm(p - cl2)
        d3 = np.linalg.norm(p - cl3)
        d4 = np.linalg.norm(p - cl4)

        return [[cl1, d1], [cl2, d2], [cl3, d3], [cl4, d4]]


if __name__ == "__main__":
    arena = Arena([0, 0], 10, 10)
    dist = arena.getNearestArenaPoint([2, 2])
    print(dist)
