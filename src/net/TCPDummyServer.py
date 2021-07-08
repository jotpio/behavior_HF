from socket import  *
import threading
import json
import sys

class TCPDummyServer():

    def __init__(self):
        print("POSSERVER: Starting dummy position server!")
        self.host = "127.0.0.1"
        self.port = 13000
        # self.socket = socket(AF_INET, SOCK_STREAM)

    def run_thread(self):
        print("POSSERVER: Started Thread!")
        
        while True:
            self.socket = socket(AF_INET, SOCK_STREAM)
            self.socket.bind((self.host, self.port))

            try:    
                self.socket.listen() # enable server to accept connections
                print("POSSERVER: Waiting for connection...")
                self.conn, address = self.socket.accept() # wait for connection
                print(f'POSSERVER: Server connected by {address}')

                while True:
                    try:
                        amount_received = 0
                        while True:
                            amount_received = 0
                            while amount_received < 4096:
                                data = self.conn.recv(4096)
                                data = json.loads(data.decode('utf-8'))
                                amount_received += len(data)
                                print('POSSERVER: Received "%s"' % data)

                    except:
                        print("POSSERVER: Socket error!")
                        break
            except:
                pass    
            finally:
                print('POSSERVER: Closing socket')
                self.socket.close()

if __name__ == '__main__':

    try:
        s = TCPDummyServer()
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


