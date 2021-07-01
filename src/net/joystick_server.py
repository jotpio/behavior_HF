import time

class JoystickServer():
    def __init__(self):
        pass
    
    def run_thread(self):
        while True:
            print("joystick", flush=True)
            time.sleep(2)
