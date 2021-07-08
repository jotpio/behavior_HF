from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import math
import numpy as np

class Arena():
    def __init__(self, anchor_point, width, height):
        self.anchor_point = anchor_point
        self.width = width
        self.height = height
        self.rect = QRectF(anchor_point[0], anchor_point[1], width, height)
        self.rectItem = QGraphicsRectItem(self.rect)

    def getRectItem(self):
        return self.rectItem
    
    #get nearest point on rect to point and distance to it
    def getNearestArenaPoints(self, point):
        ax = self.anchor_point[0]
        ay = self.anchor_point[1]

        p = np.asarray(point)

        # r1= np.asarray([ax, ay])
        # r2= np.asarray([ax + self.width, ay])
        # r3= np.asarray([ax + self.width, ay + self.height])
        # r4= np.asarray([ax, ay + self.width])

        # d1 = np.linalg.norm(np.cross(r2-r1, r1-p))/np.linalg.norm(r2-r1)
        # d2 = np.linalg.norm(np.cross(r3-r2, r2-p))/np.linalg.norm(r3-r2)
        # d3 = np.linalg.norm(np.cross(r4-r3, r3-p))/np.linalg.norm(r4-r3)
        # d4 = np.linalg.norm(np.cross(r1-r4, r4-p))/np.linalg.norm(r1-r4)

        # print(d1,d2,d3,d4)

        # closest points on four edges
        cl1 = np.asarray([p[0], ay])
        cl2 = np.asarray([ax+self.width, p[1]])
        cl3 = np.asarray([p[0], ay+self.height])
        cl4 = np.asarray([ax, p[1]])

        # distance to closest points
        d1 = np.linalg.norm(p-cl1)
        d2 = np.linalg.norm(p-cl2)
        d3 = np.linalg.norm(p-cl3)
        d4 = np.linalg.norm(p-cl4)
         
        #print(cl1, cl2, cl3, cl4)
        #print(d1,d2,d3,d4)

        return [[cl1, d1], [cl2, d2],[cl3, d3],[cl4, d4]]

if __name__ == '__main__':
    arena = Arena([0,0],10,10)
    dist = arena.getNearestArenaPoint([2,2])
    print(dist)