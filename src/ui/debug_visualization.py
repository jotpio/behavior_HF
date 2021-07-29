import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from src.models.fish import Fish

class DebugVisualization(QObject):
    def __init__(self):
        super().__init__()

        self.fish_ellipses = []
        self.arena = None

        self.show_zor = True
        self.show_zoo = True
        self.show_zoa = True

        self.app = QApplication(sys.argv)
        self.window = QWidget()
        self.window.setWindowTitle('Parameter window')
        self.window.setGeometry(100, 100, 200, 200)
        self.window.move(60, 15)
        self.layout = QVBoxLayout()
        title_label = QLabel('<h1>Parameter Window</h1>')
        self.layout.addWidget(title_label)
        title_label.move(60, 15)

        self.window.setLayout(self.layout)
        self.window.show()

        # Visualization
        self.viz_window = QWidget()
        self.viz_window.setWindowTitle('Visualization window')
        self.viz_layout = QVBoxLayout()
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.view.setSceneRect(0,0,1000,1000)
        sceneRect = self.view.sceneRect()
        # self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.viz_layout.addWidget(self.view)    
        self.viz_window.setLayout(self.viz_layout)
        self.viz_window.show()

        self.view.fitInView(QRectF(sceneRect.x()-100, sceneRect.y()-100, sceneRect.width()+200, sceneRect.height()+200), Qt.KeepAspectRatio)

    def createEllipse(self, posx, posy, rot, zor=0, zoo=0, zoa=0, width=5, height=15):
        ellipse = QGraphicsEllipseItem(-width/2, -height/2, width, height)
        ellipse.setPos(posx, posy)
        ellipse.setRotation(rot+90)
        ellipse.setPen(QPen(QColor('black')))
        ellipse.setBrush(QBrush(QColor('black')))

        if(zor > 0 and self.show_zor):
            e_zor = QGraphicsEllipseItem(-zor, -zor, zor*2, zor*2, parent=ellipse)
            e_zor.setPen(QPen(QColor('red')))
        if(zoo > 0 and self.show_zoo):
            e_zoo = QGraphicsEllipseItem(-zoo, -zoo, zoo*2, zoo*2, parent=ellipse)
            e_zoo.setPen(QPen(QColor('blue')))
        if(zoa > 0 and self.show_zoa):
            e_zoa = QGraphicsEllipseItem(-zoa, -zoa, zoa*2, zoa*2, parent=ellipse)
            e_zoa.setPen(QPen(QColor('green')))
        return ellipse

    def create_robot_shape(self, posx, posy, rot, zor=0, zoo=0, zoa=0, width=5, height=20):
        rect = QGraphicsRectItem(-width/2, -height/2, width, height)
        rect.setPos(posx, posy)
        rect.setRotation(rot+90)
        pen = QPen(QColor('red'),3)
        pen.setJoinStyle(Qt.RoundJoin)
        rect.setPen(pen)
        rect.setBrush(QBrush(QColor('red')))

        if(zor > 0 and self.show_zor):
            e_zor = QGraphicsEllipseItem(-zor, -zor, zor*2, zor*2, parent=rect)
            e_zor.setPen(QPen(QColor('red')))
        if(zoo > 0 and self.show_zoo):
            e_zoo = QGraphicsEllipseItem(-zoo, -zoo, zoo*2, zoo*2, parent=rect)
            e_zoo.setPen(QPen(QColor('blue')))
        if(zoa > 0 and self.show_zoa):
            e_zoa = QGraphicsEllipseItem(-zoa, -zoa, zoa*2, zoa*2, parent=rect)
            e_zoa.setPen(QPen(QColor('green')))
        return rect

    def update_ellipses(self, robot, fish):
        print("update shapes")
        self.fish_ellipses = [self.createEllipse(f.pos[0], f.pos[1], f.ori, f.zor, f.zoo, f.zoa) for f in fish]
        self.robot_shape = self.create_robot_shape(robot.pos[0], robot.pos[1], robot.ori, robot.zor, robot.zoo, robot.zoa)
        self.scene.clear()
        for e in self.fish_ellipses: self.scene.addItem(e)
        self.scene.addItem(self.robot_shape)
        self.setArena(self.arena)

    def update_view(self, agents):
        # print("update vis")
        for idx, a in enumerate(agents):
            if a[2] == -1: #id
                self.robot_shape.setRotation(a[1]+90)
                self.robot_shape.setPos(a[0][0],a[0][1])
            else:
                self.fish_ellipses[idx-1].setRotation(a[1]+90)
                self.fish_ellipses[idx-1].setPos(a[0][0],a[0][1])

    def setArena(self, arena):
        self.arena = arena
        borders = QGraphicsRectItem(0, 0, arena.width, arena.height)
        pen = QPen(QColor('black'))
        pen.setWidth(4)
        borders.setPen(pen)
        self.scene.addItem(borders)

    def change_zones(self, zones):
        self.show_zor = zones[0]
        self.show_zoo = zones[1]
        self.show_zoa = zones[2]

    def app_exec(self):
        sys.exit(self.app.exec_())