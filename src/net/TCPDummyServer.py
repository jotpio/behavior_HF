from socket import *
import threading
import json
import sys
import time


class TCPDummyServer:
    def __init__(self):
        print("POSSERVER: Starting dummy position server!")
        self.host = "127.0.0.1"
        self.port = 13000
        self.counter = 0
        self.connected = False
        # self.socket = socket(AF_INET, SOCK_STREAM)

    def run_thread(self):
        print("POSSERVER: Started Thread!")

        while True:
            try:
                print("new socket binding")
                self.socket = socket(AF_INET, SOCK_STREAM)
                self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                self.socket.bind((self.host, self.port))
            except:
                print(f"POSSERVER: {self.port} already in use!")
                if self.socket:
                    if self.connected:
                        self.socket.shutdown(1)
                    self.socket.close()
                    self.socket = None
                time.sleep(0.3)
                continue

            try:
                print("listening...")
                self.socket.listen()  # enable server to accept connections
                print("POSSERVER: Waiting for connection...")
                self.conn, address = self.socket.accept()  # wait for connection
                self.connected = True
                print(f"POSSERVER: Server connected by {address}")

                while self.connected:
                    try:
                        amount_received = 0
                        while self.connected:
                            amount_received = 0
                            while amount_received < 8192:
                                data = self.conn.recv(8192).decode("utf-8")
                                print(data)
                                # data = json.loads(data.decode("utf-8"))
                                amount_received += len(data)
                                print('POSSERVER: Received "%s"' % data)
                                self.counter += 1

                                if self.counter == 10:
                                    self.counter = 0
                                    if self.socket:
                                        self.conn.sendall(
                                            "end connection".encode("utf-8")
                                        )
                                        self.socket.shutdown(SHUT_RDWR)
                                        self.socket.close()
                                        self.socket = None
                                    self.connected = False
                                    break

                    except:
                        print("POSSERVER: Socket error!")
                        if self.socket:
                            self.socket.shutdown(SHUT_RDWR)
                            self.socket.close()
                            self.socket = None
                        self.connected = False
                        break
            except:
                print("POSSERVER: Closing socket")
                if self.socket:
                    # self.socket.shutdown(SHUT_WR)
                    self.socket.close()
                    self.socket = None
                self.connected = False


if __name__ == "__main__":

    try:
        s = TCPDummyServer()
        thread = threading.Thread(target=s.run_thread)
        thread.daemon = True
        thread.start()
        # thread.join()
        while thread.is_alive():
            thread.join(1)  # not sure if there is an appreciable cost to this.

    except (KeyboardInterrupt, SystemExit):
        print("\n! Received keyboard interrupt, quitting threads.\n")
        s.socket.close()
        sys.exit()

