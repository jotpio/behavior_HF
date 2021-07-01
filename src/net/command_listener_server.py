import time

class CommandListenerServer():
    def __init__(self):
        pass

    def run_thread(self):
        while True:
            print("command", flush=True)
            time.sleep(2)