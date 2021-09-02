from socket import  *
import json
import threading
import random
import sys
import time

class DummyCommandClient():
    def __init__(self, config=None):
        print("DUMMY COMMAND CLIENT: Starting dummy command client!", flush=True)
        self.config = config
        self.host = "127.0.0.1"
        self.port = config['NETWORK']['command_port'] if config is not None else 13001
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.server_address = (self.host, self.port)
        self.connected=False

    def run_thread(self):
        print("DUMMY COMMAND CLIENT: Started Thread!")
        while not self.connected:
            try:
                self.socket = socket(AF_INET, SOCK_STREAM)
                self.socket.connect(self.server_address)
                self.connected = True
                print('DUMMY COMMAND CLIENT: Connecting to %s port %s' % self.server_address)
            except Exception as e:
                pass #Do nothing, just try again
            while self.connected:
                try: 
                    self.send_com()
                    time.sleep(10)
                except:
                    print("DUMMY COMMAND CLIENT: Socket closed!")
                    self.connected = False
                    self.socket.close()
                    self.socket = None
                    break

    def send_com(self, dir=None):
        try:
            if self.connected:
                print("DUMMY COMMAND CLIENT: Sending commands", flush=True)
                command = ['control_robot', bool(random.getrandbits(1))]
                dump = json.dumps(command).encode('utf-8')
                self.socket.sendall(dump)
        except:
            self.connected = False
            "DUMMY COMMAND CLIENT: Socket error!"

if __name__ == '__main__':

    try:
        s = DummyCommandClient()
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