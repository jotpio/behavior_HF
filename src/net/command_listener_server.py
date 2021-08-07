from socket import  *
import threading
import json
import sys
from PyQt5.QtCore import (Qt, pyqtSignal, QObject)

class CommandListenerServer(QObject):

    send_command = pyqtSignal(list, name="send_command")

    def __init__(self, parent, config=None):
        print("COMSERVER: Starting command server!")
        super().__init__()  
        self.config = config
        self.host = "127.0.0.1"
        self.port = config['NETWORK']['command_port'] if config is not None else 13001
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.parent_behavior = parent
        self.send_command.connect(self.parent_behavior.queue_command, Qt.QueuedConnection)


    def run_thread(self):
        print("COMSERVER: Started Thread!")
        
        while True:
            self.socket = socket(AF_INET, SOCK_STREAM)
            self.socket.bind((self.host, self.port))

            try:    
                self.socket.listen() # enable server to accept connections
                print("COMSERVER: Waiting for connection...")
                self.conn, address = self.socket.accept() # wait for connection
                print(f'COMSERVER: Server connected by {address}')

                while True:
                    try:
                        amount_received = 0
                        while True:
                            amount_received = 0
                            while amount_received < 4096:
                                data = self.conn.recv(4096)
                                data = json.loads(data.decode('utf-8'))
                                amount_received += len(data)
                                print('COMSERVER: Received "%s"' % data)

                                self.send_command.emit(data)

                    except:
                        print("COMSERVER: Socket error!")
                        break
            except:
                pass    
            finally:
                print('COMSERVER: Closing socket')
                self.socket.close()

if __name__ == '__main__':

    try:
        s = CommandListenerServer()
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