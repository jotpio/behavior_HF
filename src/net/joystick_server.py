from socket import  *
import threading
import json
import sys
from PyQt5.QtCore import (Qt, pyqtSignal, QObject)


class JoystickServer(QObject):
    send_robodir = pyqtSignal(list, name="send_robodir")

    def __init__(self, parent, config=None):
        print("JOYSERVER: Starting joystick server!", flush=True)
        super().__init__()  
        self.config = config
        self.host = "127.0.0.1"
        self.port = config['NETWORK']['joystick_port'] if config is not None else 13002
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.parent_behavior = parent
        self.send_robodir.connect(self.parent_behavior.change_robodir, Qt.QueuedConnection)

    def run_thread(self):
        print("JOYSERVER: Started Thread!")
        
        while True:
            self.socket = socket(AF_INET, SOCK_STREAM)
            self.socket.bind((self.host, self.port))

            try:    
                self.socket.listen() # enable server to accept connections
                print("JOYSERVER: Waiting for connection...")
                self.conn, address = self.socket.accept() # wait for connection
                print(f'JOYSERVER: Server connected by {address}')

                while True:
                    try:
                        amount_received = 0
                        while True:
                            amount_received = 0
                            while amount_received < 4096:
                                data = self.conn.recv(4096)
                                data = json.loads(data.decode('utf-8'))
                                amount_received += len(data)
                                # print('JOYSERVER: Received "%s"' % data)
                                if not self.debug:
                                    self.send_robodir.emit(data)
                    except:
                        print("JOYSERVER: Socket error!")
                        break
            except:
                pass    
            finally:
                print('JOYSERVER: Closing socket')
                self.socket.close()

if __name__ == '__main__':

    try:
        s = JoystickServer()
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