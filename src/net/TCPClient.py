import socket
import json


class TCPClient():

    def __init__(self):
        # SOURCE: https://pymotw.com/2/socket/tcp.html
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        self.host = "127.0.0.1"
        self.port = 13000
        self.server_address = (self.host, self.port)

    def run_thread(self):    
        print('POSCLIENT: connecting to %s port %s' % self.server_address)
        self.sock.connect(self.server_address)

        try:
            # # Send data
            # message = "Here's a new message."
            # byteMessage = message.encode('utf-8')
            # print('CLIENT: sending "%s"' % message)
            # self.sock.sendall(byteMessage)

            # Look for the response
            amount_received = 0
            # amount_expected = 1024
            
            while True:
                amount_received = 0
                while amount_received < 1024:
                    data = self.sock.recv(1024)
                    data = json.loads(data.decode('utf-8'))
                    amount_received += len(data)
                    print('POSCLIENT: Received "%s"' % data)

        finally:
            print('POSCLIENT: Closing socket')
            self.sock.close()

if __name__ == '__main__':
    c = TCPClient()
    c.run_thread()