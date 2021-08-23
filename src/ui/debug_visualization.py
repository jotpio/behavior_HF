import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from src.models.fish import Fish


class DebugVisualization(QObject):
    def __init__(self, config):
        super().__init__()

        self.config = config

        self.fish_ellipses = []
        self.arena = None

        self.show_zor = True
        self.show_zoo = True
        self.show_zoa = True
        self.show_vision_cones = False
        self.dark_mode = True

        self.app = QApplication(sys.argv)
        self.window = QWidget()
        self.window.setWindowTitle("Parameter window")
        self.window.setGeometry(100, 100, 200, 200)
        self.window.move(60, 15)
        self.layout = QVBoxLayout()
        title_label = QLabel("<h1>Parameter Window</h1>")
        self.layout.addWidget(title_label)
        title_label.move(60, 15)

        self.window.setLayout(self.layout)
        self.window.show()

        # Visualization
        self.viz_window = QWidget()
        self.viz_window.setWindowTitle("Visualisation window")
        self.viz_layout = QVBoxLayout()
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.view.setSceneRect(
            0, 0, self.config["ARENA"]["height"], self.config["ARENA"]["width"]
        )
        # background_color = "black" if self.dark_mode else "white"
        color = QColor()
        if self.dark_mode:
            color.setRgb(0, 0, 0, 230)
        else:
            color.setRgbF(255, 255, 255, 255)
        self.view.setBackgroundBrush(QBrush(color))
        sceneRect = self.view.sceneRect()
        # self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.viz_layout.addWidget(self.view)
        self.viz_window.setLayout(self.viz_layout)
        self.viz_window.show()

        self.view.fitInView(
            QRectF(
                sceneRect.x() - 100,
                sceneRect.y() - 100,
                sceneRect.width() + 200,
                sceneRect.height() + 200,
            ),
            Qt.KeepAspectRatio,
        )

    def createEllipse(self, posx, posy, rot, zor=0, zoo=0, zoa=0, width=5, height=15):
        ellipse = QGraphicsEllipseItem(-width / 2, -height / 2, width, height)
        ellipse.setPos(posx, posy)
        ellipse.setRotation(rot + 90)
        color = "white" if self.dark_mode else "black"
        ellipse.setPen(QPen(QColor(color)))
        ellipse.setBrush(QBrush(QColor(color)))

        if zor > 0 and self.show_zor:
            e_zor = QGraphicsEllipseItem(-zor, -zor, zor * 2, zor * 2, parent=ellipse)
            color_name = "orangered" if self.dark_mode else "red"
            color = QColor()
            color.setNamedColor(color_name)
            r_pen = QPen(color)
            r_pen.setWidth(2)
            e_zor.setPen(r_pen)
        if zoo > 0 and self.show_zoo:
            e_zoo = QGraphicsEllipseItem(-zoo, -zoo, zoo * 2, zoo * 2, parent=ellipse)
            color_name = "cyan" if self.dark_mode else "blue"
            color = QColor()
            color.setNamedColor(color_name)
            o_pen = QPen(color)
            o_pen.setWidth(2)
            e_zoo.setPen(o_pen)
        if zoa > 0 and self.show_zoa:
            e_zoa = QGraphicsEllipseItem(-zoa, -zoa, zoa * 2, zoa * 2, parent=ellipse)
            color_name = "palegreen" if self.dark_mode else "green"
            color = QColor()
            color.setNamedColor(color_name)
            a_pen = QPen(color)
            a_pen.setWidth(2)
            e_zoa.setPen(a_pen)

        # vision
        if self.show_vision_cones:
            pie_vision = QGraphicsEllipseItem(
                -zoa, -zoa, zoa * 2, zoa * 2, parent=ellipse
            )
            pie_vision.setStartAngle(
                90 * 16 - self.config["DEFAULTS"]["vision_angle"] * 8
            )
            pie_vision.setSpanAngle(self.config["DEFAULTS"]["vision_angle"] * 16)
            pie_vision.setBrush(QBrush(QColor(0, 0, 0, 50)))
        return ellipse

    def create_robot_shape(
        self, posx, posy, rot, zor=0, zoo=0, zoa=0, width=5, height=20
    ):
        rect = QGraphicsRectItem(-width / 2, -height / 2, width, height)
        rect.setPos(posx, posy)
        rect.setRotation(rot + 90)
        pen = QPen(QColor("red"), 3)
        pen.setJoinStyle(Qt.RoundJoin)
        rect.setPen(pen)
        rect.setBrush(QBrush(QColor("red")))

        # zones
        if zor > 0 and self.show_zor:
            e_zor = QGraphicsEllipseItem(-zor, -zor, zor * 2, zor * 2, parent=rect)
            color_name = "orangered" if self.dark_mode else "red"
            color = QColor()
            color.setNamedColor(color_name)
            r_pen = QPen(color)
            r_pen.setWidth(2)
            e_zor.setPen(r_pen)
        if zoo > 0 and self.show_zoo:
            e_zoo = QGraphicsEllipseItem(-zoo, -zoo, zoo * 2, zoo * 2, parent=rect)
            color_name = "cyan" if self.dark_mode else "blue"
            color = QColor()
            color.setNamedColor(color_name)
            o_pen = QPen(color)
            o_pen.setWidth(2)
            e_zoo.setPen(o_pen)
        if zoa > 0 and self.show_zoa:
            e_zoa = QGraphicsEllipseItem(-zoa, -zoa, zoa * 2, zoa * 2, parent=rect)
            color_name = "palegreen" if self.dark_mode else "green"
            color = QColor()
            color.setNamedColor(color_name)
            a_pen = QPen(color)
            a_pen.setWidth(2)
            e_zoa.setPen(a_pen)

        # vision
        if self.show_vision_cones:
            pie_vision = QGraphicsEllipseItem(-zoa, -zoa, zoa * 2, zoa * 2, parent=rect)
            pie_vision.setStartAngle(
                90 * 16 - self.config["DEFAULTS"]["vision_angle"] * 8
            )
            pie_vision.setSpanAngle(self.config["DEFAULTS"]["vision_angle"] * 16)

        return rect

    def update_ellipses(self, robot, fish):
        print("update shapes")
        self.fish_ellipses = [
            self.createEllipse(f.pos[0], f.pos[1], f.ori, f.zor, f.zoo, f.zoa)
            for f in fish
        ]
        self.robot_shape = self.create_robot_shape(
            robot.pos[0], robot.pos[1], robot.ori, robot.zor, robot.zoo, robot.zoa
        )
        self.scene.clear()
        for e in self.fish_ellipses:
            self.scene.addItem(e)
        self.scene.addItem(self.robot_shape)
        self.setArena(self.arena)

    def update_view(self, agents):
        # print("update vis")
        for idx, a in enumerate(agents):
            if a["id"] == 0:  # id
                self.robot_shape.setRotation(a["orientation"] + 90)
                self.robot_shape.setPos(a["position"][0], a["position"][1])
            else:
                self.fish_ellipses[idx - 1].setRotation(a["orientation"] + 90)
                self.fish_ellipses[idx - 1].setPos(a["position"][0], a["position"][1])

    def setArena(self, arena):
        self.arena = arena
        borders = QGraphicsRectItem(0, 0, arena.width, arena.height)
        color = "white" if self.dark_mode else "black"
        pen = QPen(QColor(color))
        pen.setWidth(4)
        borders.setPen(pen)
        self.scene.addItem(borders)

        # repulsion zone
        repulsion = self.config["ARENA"]["repulsion"]
        repulsion_zone = QPainterPath()
        repulsion_zone.addRect(0, 0, arena.width, arena.height)
        repulsion_zone.addRect(
            repulsion,
            repulsion,
            arena.width - (repulsion * 2),
            arena.height - (repulsion * 2),
        )
        brush = QBrush(QColor(255, 0, 0, 25))  # r g b a
        self.scene.addPath(repulsion_zone, brush=brush)

    def change_zones(self, zones):
        self.show_zor = zones[0]
        self.show_zoo = zones[1]
        self.show_zoa = zones[2]

    def toggle_vision_cones(self, bool):
        self.show_vision_cones = bool

    def toggle_dark_mode(self, bool):
        self.dark_mode = bool
        color = QColor()
        if self.dark_mode:
            color.setRgb(0, 0, 0, 230)
        else:
            color.setRgb(255, 255, 255, 255)
        self.view.setBackgroundBrush(QBrush(color))

    def app_exec(self):
        sys.exit(self.app.exec_())
