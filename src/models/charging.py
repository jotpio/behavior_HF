try:
    from robotracker import (
        PythonBehavior,
        RobotActionFlush,
        RobotActionHalt,
        RobotActionToTarget,
        RobotActionDirect,
        RobotActionTurningForward,
    )
except:
    print("CHARGING: no RT found")

import numpy as np
import sys
import os
import logging


def charging_routine(
    behavior_robot, curr_action, charger_pos, network_controller, charger_target
):
    """Implements the automatic charging routine.
    (1) check if currently charging and not full -> halt robot
    (2) check if fully charged and at ch. station -> drive away from charging station
    (3) check if voltage low  and not charging -> go to charging station
    else: do nothing

    Args:
        behavior_robot (_type_): _description_
        curr_action (_type_): _description_
        charger_pos (_type_): _description_
        network_controller (_type_): _description_
        charger_target (_type_): _description_

    Returns:
        _type_: _description_
    """
    try:
        action = []

        # check if charging and not at full charge
        if behavior_robot.charging and not behavior_robot.full_charge:
            logging.info("CHARGING: Charging!")
            # self.behavior_robot.go_to_charging_station = (
            #     False  # arrived at charging station and is charging
            # )

            if not curr_action:
                action = [
                    ["flush", [behavior_robot.uid]],
                    ["halt", [behavior_robot.uid, 0]],
                ]
                return action

        # done with charging: go away from charging port
        if behavior_robot.full_charge:
            behavior_robot.go_to_charging_station = False

            close_to_ch_st = check_if_close_to_charging_station(
                behavior_robot, charger_pos
            )

            # if currently charging: drive backwards until not charging anymore
            if behavior_robot.charging:
                logging.info(
                    "CHARGING: Done charging, trying to detach from charging station..."
                )
                if not curr_action:
                    action = [
                        ["direct", [behavior_robot.uid, 0, -5.0, -5.0]],
                    ]
                    return action
            # check if near charging station (for example at startup if full)
            elif close_to_ch_st:
                logging.info(
                    "CHARGING: Too close to charging station rotate until facing into tank"
                )
                # check orientation and rotate so its facing away from the charger
                rot = behavior_robot.ori
                right_rot = rot < 170 and rot > 90
                # logging.info(rot)

                # rotate until correct orientation away from charger
                if not right_rot and not curr_action:
                    action = [
                        ["direct", [behavior_robot.uid, 0, 2.0, -4.0]],
                    ]
                    return action

            else:
                # network_controller.charge_command.emit(
                #     {"command": "done charging", "args": [0]}
                # )
                # logging.info(
                #     "CHARGING: full but not charging and not at charging station"
                # )
                pass

        # if not at charging station go there if voltage low
        if behavior_robot.go_to_charging_station:
            # network_controller.charge_command.emit(
            #     {"command": "robot charging", "args": [0]}
            # )

            logging.info("CHARGING: Go to charging station")

            # check if at right y position in front of charger
            pos = behavior_robot.pos
            pos_y_difference = np.abs(pos[1] - charger_pos[1])
            if pos_y_difference < 50:
                right_posy = True
            else:
                right_posy = False
            # go to right position in front of charger
            if not right_posy and not curr_action:
                action = [
                    ["flush", [behavior_robot.uid]],
                    [
                        "target",
                        [
                            behavior_robot.uid,
                            0,
                            (charger_target[0], charger_target[1]),
                        ],
                    ],
                ]
                return action

            # logging.info("Robot at right y pos")

            # check rotation
            rot = behavior_robot.ori
            right_rot = np.abs(rot) < 8

            # rotate until correct orientation
            if not right_rot and not curr_action:
                action = [
                    ["direct", [behavior_robot.uid, 0, 3.0, -3.0]],
                ]
                return action
            logging.info("CHARGING: Robot to charge and at right orientation")

            # drive forwards into charger
            # check first if at charger position
            pos_x_difference = pos[0] - charger_pos[0]
            if pos_x_difference >= 0:
                right_posx = True
            else:
                right_posx = False

            if not right_posx and not curr_action:
                # drive slowly towards charger
                action = [
                    ["direct", [behavior_robot.uid, 0, 4.0, 4.0]],
                ]
                return action
            logging.info("CHARGING: Robot to charge and at right x pos!")

        # everything is okay, robot can drive freely
        else:
            # logging.info("BEHAVIOR: Does not need to be charged...")
            pass

        return action
    except Exception as e:
        logging.error(f"CHARGING: Error in charging routine!")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error(exc_type, fname, exc_tb.tb_lineno)


def check_if_close_to_charging_station(behavior_robot, charger_pos):
    close_to_charging_station = np.all(
        np.abs(behavior_robot.pos - np.asarray(charger_pos)) < 300
    )
    return close_to_charging_station
