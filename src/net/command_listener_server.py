from socket import *
import threading
import json
import sys
from PyQt5.QtCore import Qt, pyqtSignal, QObject
import time

from src.net.base.server import ServerListenerThread


class CommandListenerServer(ServerListenerThread):
    send_command = pyqtSignal(list, name="send_command")

    def __init__(self, parent, config=None):
        super().__init__(parent, "command", config=config)
        self.send_command.connect(
            self.parent_behavior.queue_command, Qt.QueuedConnection
        )

    def run_thread(self):
        while True:
            successful = self.start_server()
            # retry server start if not successful
            if not successful:
                continue

            # do things while connected
            while self.connected:
                try:
                    amount_received = 0
                    while amount_received < 4096:
                        data = self.conn.recv(4096).decode("utf-8")

                        if len(data) == 0:
                            self.print("Empty data; closing socket!")
                            self.close_socket()
                            break

                        if data == "end connection":
                            self.print("closing socket!")
                            self.close_socket()
                            break

                        try:
                            data = json.loads(data)
                        except:
                            self.print(f"Error decoding message: {data}")
                            break
                        amount_received += len(data)
                        self.print(f"Received {data}")

                        self.send_command.emit(data)

                        # send received message to unity
                        try:
                            message = "received"
                            self.conn.sendall(message.encode("utf-8"))
                        except:
                            self.print(f"Error sending 'received' message!")
                            break

                except:
                    self.print("Socket error!")
                    self.close_socket()
                    break


# class CommandListenerServer(QObject):

#     send_command = pyqtSignal(list, name="send_command")

#     def __init__(self, parent, config=None):
#         print("COMSERVER: Starting command server!")
#         super().__init__()
#         self.config = config
#         self.host = "127.0.0.1"
#         self.port = config["NETWORK"]["command_port"] if config is not None else 13001
#         self.socket = socket(AF_INET, SOCK_STREAM)
#         self.parent_behavior = parent
#         self.send_command.connect(
#             self.parent_behavior.queue_command, Qt.QueuedConnection
#         )
#         self.connected = False

#     def run_thread(self):
#         print("COMSERVER: Started Thread!")

#         while True:
#             try:
#                 self.socket = socket(AF_INET, SOCK_STREAM)
#                 self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
#                 self.socket.bind((self.host, self.port))
#             except:
#                 print(f"COMSERVER: {self.port} already in use!")
#                 if self.socket:
#                     if self.connected:
#                         self.socket.shutdown(1)
#                         self.connected = False
#                     self.socket.close()
#                     self.socket = None
#                 time.sleep(0.3)
#                 continue

#             try:
#                 self.socket.listen()  # enable server to accept connections
#                 print("COMSERVER: Waiting for connection...")
#                 self.conn, address = self.socket.accept()  # wait for connection
#                 print(f"COMSERVER: Server connected by {address}")
#                 self.connected = True
#                 while True:
#                     try:
#                         amount_received = 0
#                         while True:
#                             amount_received = 0
#                             while amount_received < 4096:
#                                 data = self.conn.recv(4096)
#                                 try:
#                                     data = json.loads(data.decode("utf-8"))
#                                 except:
#                                     print("COMSERVER: Error decoding message!")
#                                 amount_received += len(data)
#                                 # print('COMSERVER: Received "%s"' % data)

#                                 self.send_command.emit(data)

#                     except:
#                         print("COMSERVER: Socket error!")

#                         if self.socket and not self.connected:
#                             self.socket.shutdown(SHUT_WR)
#                             self.socket.close()
#                             self.connected = False
#                         self.socket = None
#                         break
#             except:
#                 pass
#             finally:
#                 print("COMSERVER: Closing socket")
#                 if self.socket and not self.connected:
#                     self.socket.shutdown(SHUT_WR)
#                     self.socket.close()
#                     self.connected = False
#                 self.socket = None


# if __name__ == "__main__":

#     try:
#         s = CommandListenerServer()
#         thread = threading.Thread(target=s.run_thread)
#         thread.daemon = True
#         thread.start()
#         # thread.join()
#         while thread.is_alive():
#             thread.join(1)  # not sure if there is an appreciable cost to this.

#     except (KeyboardInterrupt, SystemExit):
#         print("\n! Received keyboard interrupt, quitting threads.\n")
#         s.socket.shutdown(
#             SHUT_RDWR
#         )  # SHUT_RDWR: further sends and receives are disallowed
#         s.socket.close()
#         sys.exit()
