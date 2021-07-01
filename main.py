import threading
import sys
from src.net.TCPDummyServer import TCPDummyServer
from src.net.TCPClient import TCPClient
from Behavior import Behavior
from src.ui.debug_visualization import DebugVisualization
from PyQt5.QtWidgets import QGraphicsEllipseItem, QLayout, QVBoxLayout, QHBoxLayout, QPushButton, QSpinBox, QLabel, QApplication, QWidget
from PyQt5.QtCore import *

class Main():
    def __init__(self):
        # run TCP server to send and receive dummy data 
        # print("running dummy server")
        # dserver = TCPDummyServer()
        # s_thread = threading.Thread(target = dserver.run_thread)
        # s_thread.daemon = True
        # s_thread.start()

        # run behavior/client thread to get joystick movement and send positional data
        print("running behavior / tcp client")
        
        #debug vis 
        # setup debug visualization
        self.debug_vis = DebugVisualization()

        #behavior
        # run behavior thread
        self.behavior = Behavior(layout=self.debug_vis.layout, DEBUG_VIS=self.debug_vis)
        self.behavior.update_positions.connect(self.debug_vis.update_view, Qt.QueuedConnection)
        self.behavior.update_ellipses.connect(self.debug_vis.update_ellipses, Qt.QueuedConnection)
        self.behavior.update_ellipses.emit(self.behavior.fish)

        b_thread = threading.Thread(target = self.behavior.run_thread)
        b_thread.daemon = True
        b_thread.start()


        # #dummy pos client
        # dclient = TCPClient()
        # c_thread = threading.Thread(target = dclient.run_thread)
        # c_thread.daemon = True
        # c_thread.start()

        self.debug_vis.app_exec()

if __name__ == '__main__':
    Main()

