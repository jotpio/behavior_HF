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
import sys,os

def charging_routine(robot, behavior_robot, curr_action, charger_pos, network_controller, charger_target):

    try:
        action = []

        # check if charging and not at full charge
        if behavior_robot.charging and not behavior_robot.full_charge:
            print("BEHAVIOR: Charging!")
            # self.behavior_robot.go_to_charging_station = (
            #     False  # arrived at charging station and is charging
            # )

            if not curr_action:
                action = [
                    RobotActionFlush(robot.uid),
                    RobotActionHalt(
                        robot.uid, 0
                    ),  # TODO: dont halt but drive slowly forwards maybe?
                ]
                return action

        # done with charging: go away from charging port
        if behavior_robot.full_charge:

            close_to_ch_st = check_if_close_to_charging_station(behavior_robot, charger_pos)

            # if currently charging: drive backwards until not charging anymore
            if behavior_robot.charging:
                print("BEHAVIOR: Done charging")
                if not curr_action:
                    action = [
                        RobotActionDirect(robot.uid, 0, -7.0, -7.0),
                    ]
                    network_controller.charge_command.emit(
                        {"command": "done charging", "args": [0]}
                    )
                    return action
            # check if near charging station (for example at startup if full)
            elif close_to_ch_st:
                # check orientation and rotate so its facing the charger
                rot = behavior_robot.ori
                right_rot = np.abs(rot) > 170
                # rotate until correct orientation
                if not right_rot and not curr_action:
                    action = [
                        RobotActionDirect(robot.uid, 0, 3.0, -3.0),
                    ]
                    print("Robot at right orientation")
                    return action
                # if at right orientation drive backwards until not close to charging statio anymore
                elif right_rot and not curr_action:
                    action = [
                        RobotActionDirect(robot.uid, 0, -7.0, -7.0),
                    ]
                    return action
            else:
                print("BEHAVIOR: full but not charging and not at charging station")

        # if not at charging station go there if voltage low
        if behavior_robot.go_to_charging_station:
            network_controller.charge_command.emit(
                {"command": "robot charging", "args": [0]}
            )

            print("BEHAVIOR: Charging routine: go to charging station")

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
                    RobotActionFlush(robot.uid),
                    RobotActionToTarget(
                        robot.uid,
                        0,
                        (charger_target[0], charger_target[1]),
                    ),
                ]
                return action

            print("Robot at right y pos")

            # check rotation
            rot = behavior_robot.ori
            right_rot = np.abs(rot) > 175
            print(rot)
            # rotate until correct orientation
            if not right_rot and not curr_action:
                action = [
                    RobotActionDirect(robot.uid, 0, 3.0, -3.0),
                ]
                return action
            print("Robot at right orientation")

            # drive forwards into charger
            # check first if at charger position
            pos_x_difference = pos[0] - charger_pos[0]
            if pos_x_difference <= 0:
                right_posx = True
            else:
                right_posx = False

            if not right_posx and not curr_action:
                # charger_pos = self.config["CHARGER"]["position"]
                # target = charger_pos[0], charger_pos[1]
                # target = self.util.map_px_to_cm(target)

                # drive slowly towards charger
                action = [
                    RobotActionDirect(robot.uid, 0, 4.0, 4.0),
                ]
                return action
            print("Robot at right x pos!")

        # everything is okay, robot can drive freely
        else:
            # print("BEHAVIOR: Does not need to be charged...")
            pass

        return action
    except Exception as e:
        print(f"CHARGING: Error in charging routine!")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)

def check_if_close_to_charging_station(behavior_robot, charger_pos):
        close_to_charging_station = np.all(
            np.abs(behavior_robot.pos - np.asarray(charger_pos)) < 200
        )
        return close_to_charging_station
