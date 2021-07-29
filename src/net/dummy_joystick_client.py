from socket import  *
import json
import threading
import random
import sys
import time

class DummyJoystickClient():
    def __init__(self, config=None):
        print("DUMMY JOYSTICK CLIENT: Starting dummy joystick client!", flush=True)
        self.config = config
        self.host = "127.0.0.1"
        self.port = config['NETWORK']['joystick_port'] if config is not None else 13002
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.server_address = (self.host, self.port)
        self.connected=False

    def run_thread(self):
        print("DUMMY JOYSTICK CLIENT: Started Thread!")
        while not self.connected:
            try:
                self.socket = socket(AF_INET, SOCK_STREAM)
                self.socket.connect(self.server_address)
                self.connected = True
                print('DUMMY JOYSTICK CLIENT: Connecting to %s port %s' % self.server_address)
            except Exception as e:
                pass #Do nothing, just try again
            while self.connected:
                try: 
                    self.send_dir()
                    time.sleep(0.5)
                except:
                    print("DUMMY JOYSTICK CLIENT: Socket closed!")
                    self.connected = False
                    self.socket = None
                    break

    def send_dir(self, dir=None):
        try:
            if self.connected:
                print("DUMMY JOYSTICK CLIENT: Sending new robot directions", flush=True)
                new_dir = dir if dir != None else [random.uniform(-1, 1), random.uniform(-1, 1)]
                dump = json.dumps(new_dir).encode('utf-8')
                self.socket.sendall(dump)
        except:
            "DUMMY JOYSTICK CLIENT: Socket error!"

if __name__ == '__main__':

    try:
        s = DummyJoystickClient()
        thread = threading.Thread(target = s.run_thread)
        thread.daemon = True
        thread.start()
        # thread.join()
        while thread.is_alive(): 
            thread.join(1)  # not sure if there is an appreciable cost to this.

    except (KeyboardInterrupt, SystemExit):
        print('\n! Received keyboard interrupt, quitting threads.\n')
        s.socket.close()
        sys.exit()