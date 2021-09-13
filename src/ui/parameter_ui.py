from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter


class Parameter_UI(QVBoxLayout):
    def __init__(self, parent_behavior, RT_MODE):
        super().__init__()
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
            self.parent_behavior.on_random_target_clicked, Qt.QueuedConnection
        )
        self.reset_button.clicked.connect(
            self.parent_behavior.on_reset_button_clicked, Qt.QueuedConnection
        )
        self.num_fish_spinbox.valueChanged.connect(
            self.parent_behavior.on_num_fish_spinbox_valueChanged, Qt.QueuedConnection
        )
        if not self.RT_MODE:
            self.zoa_checkbox.toggled.connect(
                self.parent_behavior.on_zone_checkbox_changed, Qt.QueuedConnection
            )
            self.zoo_checkbox.toggled.connect(
                self.parent_behavior.on_zone_checkbox_changed, Qt.QueuedConnection
            )
            self.zor_checkbox.toggled.connect(
                self.parent_behavior.on_zone_checkbox_changed, Qt.QueuedConnection
            )
            self.vision_checkbox.toggled.connect(
                self.parent_behavior.on_vision_checkbox_changed, Qt.QueuedConnection
            )
            self.dark_mode_checkbox.toggled.connect(
                self.parent_behavior.on_dark_mode_checkbox_changed, Qt.QueuedConnection
            )

        self.zor_spinbox.valueChanged.connect(
            self.parent_behavior.on_zor_spinbox_valueChanged, Qt.QueuedConnection
        )
        self.zoo_spinbox.valueChanged.connect(
            self.parent_behavior.on_zoo_spinbox_valueChanged, Qt.QueuedConnection
        )
        self.zoa_spinbox.valueChanged.connect(
            self.parent_behavior.on_zoa_spinbox_valueChanged, Qt.QueuedConnection
        )

        self.auto_robot_checkbox.toggled.connect(
                self.parent_behavior.on_auto_robot_checkbox_changed, Qt.QueuedConnection
        )
        self.next_robot_step.clicked.connect(
            self.parent_behavior.on_next_robot_step_clicked, Qt.QueuedConnection
        )
        self.flush_robot_button.clicked.connect(
            self.parent_behavior.on_flush_robot_target_clicked, Qt.QueuedConnection
        )

        # configure checkboxes
        if not self.RT_MODE:
            self.zoa_checkbox.setChecked(False)
            self.zoo_checkbox.setChecked(False)
            self.zor_checkbox.setChecked(False)
            self.vision_checkbox.setChecked(False)
            self.dark_mode_checkbox.setChecked(True)
        self.auto_robot_checkbox.setChecked(True)
        self.next_robot_step.setEnabled(not self.auto_robot_checkbox.isChecked())
        self.flush_robot_button.setEnabled(not self.auto_robot_checkbox.isChecked())
