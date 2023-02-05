import threading

from PyQt5.QtCore import Qt
from src.simulation import Behavior
from src.ui.debug_visualization import DebugVisualization

import yaml
from pathlib import Path


class Main:
    def __init__(self) -> None:
        # load config file
        path = Path(__file__).parent
        self.config = yaml.safe_load(open(path / "cfg/config.yml"))
        print(self.config)
        # run behavior/client thread to get joystick movement and send positional data
        print("running behavior / tcp client")

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
            self.behavior.network_controller.update_positions.connect(
                self.debug_vis.update_view, Qt.QueuedConnection
            )
        if self.debug_vis is not None:
            self.behavior.network_controller.update_ellipses.connect(
                self.debug_vis.update_ellipses, Qt.QueuedConnection
            )
        self.behavior.network_controller.update_ellipses.emit(
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
