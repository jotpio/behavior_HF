import os
from PyQt5.QtCore import QThread
import time
import logging

FORMAT = "\t%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


class HeartbeatTimer(QThread):
    def __init__(self):
        QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run_thread(self):
        # heartbeat
        while True:
            self.heartbeat()
            time.sleep(5)  # trigger every 5 seconds

    def heartbeat(self):
        try:
            heartbeat_path = "/home/user1/RoboTracker_HF/heartbeat/RTLog.txt"
            if not os.path.isfile(heartbeat_path):
                os.mknod(heartbeat_path)
        except:
            logging.error("TIMER: Error in heartbeat!")
