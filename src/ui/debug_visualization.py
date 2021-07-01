import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

class DebugVisualization():
    def __init__(self):

        self.fish_ellipses = []

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
        self.scene.setSceneRect(0,0,1000,1000)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform);
        self.viz_layout.addWidget(self.view)    
        self.viz_window.setLayout(self.viz_layout)
        self.viz_window.show()

    def createEllipse(self, posx, posy, width=10, height=30):
        print("create ellipse")
        ellipse = QGraphicsEllipseItem(-width/2, -height/2, width, height)
        ellipse.setPos(posx, posy)
        ellipse.setPen(QPen(QColor('black')))
        ellipse.setBrush(QBrush(QColor('black')))
        return ellipse

    def update_ellipses(self, fish):
        print("update ellipses")
        self.fish_ellipses = [self.createEllipse(f[0], f[1]) for f in fish]
        self.scene.clear()
        for e in self.fish_ellipses: self.scene.addItem(e)

    def update_view(self, fish):
        # print("update vis")
        for idx, f in enumerate(fish):
            self.fish_ellipses[idx].setPos(f[0],f[1])
            self.fish_ellipses[idx].setRotation(f[2]+90)

    def app_exec(self):
        sys.exit(self.app.exec_())