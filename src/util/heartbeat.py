import os
from PyQt5.QtCore import QThread
import time


class HeartbeatTimer(QThread):
    def __init__(self, config):
        QThread.__init__(self)
        self.config = config
        self.heartbeat_path = self.config["DEFAULTS"]["heartbeat_path"]


    def __del__(self):
        self.wait()

    def run_thread(self):
        # heartbeat
        while True:
            self.heartbeat()
            time.sleep(5)  # trigger every 5 seconds

    def heartbeat(self):
        try:
            if not os.path.isfile(self.heartbeat_path):
                os.mknod(self.heartbeat_path)
        except:
            print("TIMER: Error in heartbeat!")
