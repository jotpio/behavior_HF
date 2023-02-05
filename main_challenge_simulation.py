import threading

from src.challenge_simulation import Behavior
from src.ui.debug_visualization import DebugVisualization

from PyQt5.QtCore import Qt

import yaml
from pathlib import Path


class Main:
    def __init__(self):
        # load config file
        path = Path(__file__).parent
        self.config = yaml.safe_load(open(path / "cfg/config.yml"))
        print(self.config)
        # run behavior/client thread to get joystick movement and send positional data
        print(
            "\n         ___     ___ _           _ _                         __  _                 _       _   _             \n"
            "  /\  /\/ __\   / __\ |__   __ _| | | ___ _ __   __ _  ___  / _\(_)_ __ ___  _   _| | __ _| |_(_) ___  _ __  \n"
            " / /_/ / _\    / /  | '_ \ / _` | | |/ _ \ '_ \ / _` |/ _ \ \ \ | | '_ ` _ \| | | | |/ _` | __| |/ _ \| '_ \ \n"
            "/ __  / /     / /___| | | | (_| | | |  __/ | | | (_| |  __/ _\ \| | | | | | | |_| | | (_| | |_| | (_) | | | |\n"
            "\/ /_/\/      \____/|_| |_|\__,_|_|_|\___|_| |_|\__, |\___| \__/|_|_| |_| |_|\__,_|_|\__,_|\__|_|\___/|_| |_|\n"
            "                                                |___/"
        )

        print("running challenge simulation behavior")

        # setup debug visualization
        self.debug_vis = (
            DebugVisualization(self.config)
            if self.config["DEBUG"]["visualisation"]
            else None
        )

        # behavior
        # run behavior thread
        layout = (
            self.debug_vis.layout if self.config["DEBUG"]["visualisation"] else None
        )
        self.behavior = Behavior(
            layout=layout, DEBUG_VIS=self.debug_vis, config=self.config
        )
        if self.debug_vis is not None:
            self.behavior.update_positions.connect(
                self.debug_vis.update_view, Qt.QueuedConnection
            )
        if self.debug_vis is not None:
            self.behavior.update_ellipses.connect(
                self.debug_vis.update_ellipses, Qt.QueuedConnection
            )
        self.behavior.update_ellipses.emit(
            self.behavior.behavior_robot, self.behavior.allfish
        )

        b_thread = threading.Thread(target=self.behavior.run_thread)
        b_thread.daemon = True
        b_thread.start()

        if self.debug_vis is not None:
            self.debug_vis.app_exec()
        else:
            self.behavior.app_exec()


if __name__ == "__main__":
    Main()
