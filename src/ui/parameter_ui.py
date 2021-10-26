from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpinBox, QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter

from src.util.util import Util

import random


class Parameter_UI(QVBoxLayout):
    def __init__(self, parent_behavior, RT_MODE, config):
        super().__init__()

        self.config = config
        self.util = Util(self.config)
        self.RT_MODE = RT_MODE
        self.parent_behavior = parent_behavior

        self.random_target = QPushButton(f"Drive to new random point")
        self.addWidget(self.random_target)

        # number of fish
        self.num_fish_layout = QHBoxLayout()
        num_fish_label = QLabel(f"Set number of fish:")
        self.num_fish_spinbox = QSpinBox()
        self.num_fish_spinbox.setRange(0, 1000)
        self.num_fish_spinbox.setValue(self.parent_behavior.default_num_fish)
        self.num_fish_layout.addWidget(num_fish_label)
        self.num_fish_layout.addWidget(self.num_fish_spinbox)
        self.addLayout(self.num_fish_layout)

        self.reset_button = QPushButton(f"Reset fish")
        self.addWidget(self.reset_button)


        if not self.RT_MODE:
            # zone checkboxes
            self.zoa_checkbox = QCheckBox("Show zone of attraction")
            self.zoo_checkbox = QCheckBox("Show zone of orientation")
            self.zor_checkbox = QCheckBox("Show zone of repulsion")
            self.vision_checkbox = QCheckBox("Show vision cone")
            self.dark_mode_checkbox = QCheckBox("Enable dark mode")

            self.addWidget(self.zoa_checkbox)
            self.addWidget(self.zoo_checkbox)
            self.addWidget(self.zor_checkbox)
            self.addWidget(self.vision_checkbox)
            self.addWidget(self.dark_mode_checkbox)

        # zor spinbox
        self.zor_sb_layout = QHBoxLayout()
        zor_sb_label = QLabel(f"Change zor radius:")
        self.zor_spinbox = QSpinBox()
        self.zor_spinbox.setRange(0, 2000)
        self.zor_spinbox.setValue(self.parent_behavior.zor)
        self.zor_sb_layout.addWidget(zor_sb_label)
        self.zor_sb_layout.addWidget(self.zor_spinbox)
        self.addLayout(self.zor_sb_layout)

        # zoo spinbox
        self.zoo_sb_layout = QHBoxLayout()
        zoo_sb_label = QLabel(f"Change zoo radius:")
        self.zoo_spinbox = QSpinBox()
        self.zoo_spinbox.setRange(0, 2000)
        self.zoo_spinbox.setValue(self.parent_behavior.zoo)
        self.zoo_sb_layout.addWidget(zoo_sb_label)
        self.zoo_sb_layout.addWidget(self.zoo_spinbox)
        self.addLayout(self.zoo_sb_layout)

        # zoa spinbox
        self.zoa_sb_layout = QHBoxLayout()
        zoa_sb_label = QLabel(f"Change zoa radius:")
        self.zoa_spinbox = QSpinBox()
        self.zoa_spinbox.setRange(0, 2000)
        self.zoa_spinbox.setValue(self.parent_behavior.zoa)
        self.zoa_sb_layout.addWidget(zoa_sb_label)
        self.zoa_sb_layout.addWidget(self.zoa_spinbox)
        self.addLayout(self.zoa_sb_layout)

        # target selector
        self.target_layout = QHBoxLayout()
        target_label_sel = QLabel("Select target:")
        self.target_x = QSpinBox() 
        self.target_x.setRange(0, 2000)
        self.target_x.setValue(1000)
        self.target_y = QSpinBox() 
        self.target_y.setRange(0, 2000)
        self.target_y.setValue(1000)
        self.sel_target_pb = QPushButton("Go to target")
        self.target_layout.addWidget(target_label_sel)
        self.target_layout.addWidget(self.target_x)
        self.target_layout.addWidget(self.target_y)
        self.target_layout.addWidget(self.sel_target_pb)
        self.addLayout(self.target_layout)

        #turn buttons
        self.turn_layout = QHBoxLayout()
        self.turn_left_pb = QPushButton("Turn left")
        self.turn_right_pb = QPushButton("Turn right")
        self.turn_layout.addWidget(self.turn_left_pb)
        self.turn_layout.addWidget(self.turn_right_pb)
        self.addLayout(self.turn_layout)

        #simulate charging
        self.sim_charge_pb = QPushButton("Go to charging station")
        self.addWidget(self.sim_charge_pb)

        # auto robot toggle
        self.auto_robot_checkbox = QCheckBox("Enable automatic robot movement")
        self.addWidget(self.auto_robot_checkbox)

        # next robot step
        self.next_robot_step = QPushButton("Next robot step")
        self.addWidget(self.next_robot_step)

        # flush robot target
        self.flush_robot_button = QPushButton("Flush robot target")
        self.addWidget(self.flush_robot_button)

        # connect

        self.random_target.clicked.connect(
            self.on_random_target_clicked, Qt.QueuedConnection
        )
        self.reset_button.clicked.connect(
            self.on_reset_button_clicked, Qt.QueuedConnection
        )
        self.num_fish_spinbox.valueChanged.connect(
            self.on_num_fish_spinbox_valueChanged, Qt.QueuedConnection
        )
        if not self.RT_MODE:
            self.zoa_checkbox.toggled.connect(
                self.on_zone_checkbox_changed, Qt.QueuedConnection
            )
            self.zoo_checkbox.toggled.connect(
                self.on_zone_checkbox_changed, Qt.QueuedConnection
            )
            self.zor_checkbox.toggled.connect(
                self.on_zone_checkbox_changed, Qt.QueuedConnection
            )
            self.vision_checkbox.toggled.connect(
                self.on_vision_checkbox_changed, Qt.QueuedConnection
            )
            self.dark_mode_checkbox.toggled.connect(
                self.on_dark_mode_checkbox_changed, Qt.QueuedConnection
            )

        self.zor_spinbox.valueChanged.connect(
            self.on_zor_spinbox_valueChanged, Qt.QueuedConnection
        )
        self.zoo_spinbox.valueChanged.connect(
            self.on_zoo_spinbox_valueChanged, Qt.QueuedConnection
        )
        self.zoa_spinbox.valueChanged.connect(
            self.on_zoa_spinbox_valueChanged, Qt.QueuedConnection
        )

        self.auto_robot_checkbox.toggled.connect(
                self.on_auto_robot_checkbox_changed, Qt.QueuedConnection
        )
        self.next_robot_step.clicked.connect(
            self.on_next_robot_step_clicked, Qt.QueuedConnection
        )
        self.flush_robot_button.clicked.connect(
            self.on_flush_robot_target_clicked, Qt.QueuedConnection
        )

        self.sel_target_pb.clicked.connect(
            self.on_sel_target_pb_clicked, Qt.QueuedConnection
        )

        self.turn_left_pb.pressed.connect(
            self.on_turn_left_pb_clicked, Qt.QueuedConnection
        )

        self.turn_right_pb.pressed.connect(
            self.on_turn_right_pb_clicked, Qt.QueuedConnection
        )

        self.turn_left_pb.released.connect(
            self.on_turn_left_pb_released, Qt.QueuedConnection
        )

        self.turn_right_pb.released.connect(
            self.on_turn_right_pb_released, Qt.QueuedConnection
        )

        self.sim_charge_pb.clicked.connect(
            self.on_sim_charge_pb_clicked, Qt.QueuedConnection
        )

        # configure checkboxes
        if not self.RT_MODE:
            self.zoa_checkbox.setChecked(False)
            self.zoo_checkbox.setChecked(False)
            self.zor_checkbox.setChecked(False)
            self.vision_checkbox.setChecked(False)
            self.dark_mode_checkbox.setChecked(True)
            self.sel_target_pb.setEnabled(False)
        self.auto_robot_checkbox.setChecked(not self.config["ROBOT"]["controlled_from_start"])
        self.next_robot_step.setEnabled(not self.auto_robot_checkbox.isChecked())
        self.flush_robot_button.setEnabled(not self.auto_robot_checkbox.isChecked())

    # region <UI slots>
    def on_random_target_clicked(self):
        self.parent_behavior.target = random.randint(10, 45), random.randint(10, 45)
        if self.parent_behavior.debug_vis is not None:
            self.parent_behavior.debug_vis.scene.addEllipse(
                self.util.map_cm_to_px(self.target[0]),
                self.util.map_cm_to_px(self.target[1]),
                10,
                10,
            )
        print(f"New target selected: {self.target[0]},{self.target[1]}")

    def on_reset_button_clicked(self):
        val = self.num_fish_spinbox.value()
        self.parent_behavior.com_queue.put(("reset_fish", val))
        print(f"Reseting positions of fish!")

    def on_zone_checkbox_changed(self, bool):
        if self.parent_behavior.debug_vis:
            zones = [
                self.zor_checkbox.isChecked(),
                self.zoo_checkbox.isChecked(),
                self.zoa_checkbox.isChecked(),
            ]
            self.parent_behavior.debug_vis.change_zones(zones)
            self.parent_behavior.network_controller.update_ellipses.emit(
                self.parent_behavior.behavior_robot, self.parent_behavior.allfish
            )

    def on_vision_checkbox_changed(self):
        if self.parent_behavior.debug_vis:
            self.parent_behavior.debug_vis.toggle_vision_cones(
                self.vision_checkbox.isChecked()
            )
            self.parent_behavior.network_controller.update_ellipses.emit(
                self.parent_behavior.behavior_robot, self.allfish
            )

    def on_num_fish_spinbox_valueChanged(self, val):
        self.parent_behavior.com_queue.put(("reset_fish", val))
        print(f"Setting number of fish to: {val}")

    def on_zor_spinbox_valueChanged(self, val):
        zone_dir = {"zor": val}
        self.parent_behavior.change_zones(zone_dir)

    def on_zoo_spinbox_valueChanged(self, val):
        zone_dir = {"zoo": val}
        self.parent_behavior.change_zones(zone_dir)

    def on_zoa_spinbox_valueChanged(self, val):
        zone_dir = {"zoa": val}
        self.parent_behavior.change_zones(zone_dir)

    def on_dark_mode_checkbox_changed(self):
        if self.parent_behavior.debug_vis:
            self.parent_behavior.debug_vis.toggle_dark_mode(
                self.dark_mode_checkbox.isChecked()
            )
            self.parent_behavior.network_controller.update_ellipses.emit(
                self.parent_behavior.behavior_robot, self.parent_behavior.allfish
            )

    # robot slots
    def on_auto_robot_checkbox_changed(self, val):

        self.parent_behavior.queue_command(["control_robot", not val])
        self.next_robot_step.setEnabled(not val)
        self.flush_robot_button.setEnabled(not val)

    # if auto robot movement is disabled then the next automatic robot movement target can be triggered by this button or manually by the joystick movement
    def on_next_robot_step_clicked(self):
        self.parent_behavior.trigger_next_robot_step = True

    def on_flush_robot_target_clicked(self):
        self.parent_behavior.flush_robot_target = True

    def on_sel_target_pb_clicked(self):
        target_x = self.util.map_px_to_cm(self.target_x.value())
        target_y = self.util.map_px_to_cm(self.target_y.value())
        self.parent_behavior.target = target_x, target_y
        if self.parent_behavior.debug_vis is not None:
            self.parent_behavior.debug_vis.scene.addEllipse(
                self.util.map_cm_to_px(self.parent_behavior.target[0]),
                self.util.map_cm_to_px(self.parent_behavior.target[1]),
                10,
                10,
            )
        print(f"New target selected: {self.parent_behavior.target[0]},{self.parent_behavior.target[1]}")

    def on_turn_right_pb_clicked(self):
        self.parent_behavior.turn_right = True

    def on_turn_left_pb_clicked(self):
        self.parent_behavior.turn_left = True

    def on_turn_left_pb_released(self):
        self.parent_behavior.turn_left = False

    def on_turn_right_pb_released(self):
        self.parent_behavior.turn_right = False

    def on_sim_charge_pb_clicked(self):
        print("BUTTON: Go to charging station")
        self.parent_behavior.behavior_robot.go_to_charging_station = True

    # endregion

