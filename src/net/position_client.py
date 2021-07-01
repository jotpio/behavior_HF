import time
from socket import  *
import json

class PositionClient():
    def __init__(self):
        print("POSSERVER: Starting position server!")
        # super(TCPDummyServer, self).__init__()
        self.host = "127.0.0.1"
        self.port = 13000
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.conn = None

    def run_thread(self):
        try:
            print("POSSERVER: Started Thread!")
            self.socket.bind((self.host, self.port))
            self.socket.listen()
            self.conn, address = self.socket.accept()
            print(f'POSSERVER: Server connected by {address}')

            while True:
                try: 
                    continue
                except:
                    print("POSSERVER: Socket closed!")
                    break
                
        finally:
            print('SERVER: Closing socket')
            self.socket.close()

    def send_pos(self, pos):
        if self.conn is not None:
            print("POSSERVER: sending positions", flush=True)
            self.conn.sendall(json.dumps(pos).encode('utf-8'))