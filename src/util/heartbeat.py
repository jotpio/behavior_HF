from math import exp
import os, sys
from PyQt5.QtCore import QThread
import time
import logging

FORMAT = "\t%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


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
        except Exception as e:
            logging.error("TIMER: Error in heartbeat!")
            logging.error(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(exc_type, fname, exc_tb.tb_lineno)
