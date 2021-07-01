from socket import  *
import threading
import time
import math
import random
import json
import sys

class TCPDummyClient():

    def __init__(self):
        print("POSCLIENT: Starting dummy position client!")
        self.host = "127.0.0.1"
        self.port = 13000
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.server_address = (self.host, self.port)


        #fish params
        self.fish = [[random.randint(300, 900), random.randint(300, 900), random.randint(0,360)] for i in range(10)]
        self.fish_max_speed = 10 #TODO: put this in config and GUI
        self.fish_max_turn = 5

    def run_thread(self):
        try:
            print("POSCLIENT: Started Thread!")
            self.socket.connect(self.server_address)

            print('POSCLIENT: connecting to %s port %s' % self.server_address)
            while True:
                try: 
                    #move fish randomly
                    for f in self.fish:
                        old_rotation = f[2]
                        theta = math.radians(old_rotation)
                        move_vector = (self.fish_max_speed * math.cos(theta)) + random.uniform(-self.fish_max_turn,self.fish_max_turn), (self.fish_max_speed * math.sin(theta)) + random.uniform(-self.fish_max_turn,self.fish_max_turn)
                        new_rotation = math.degrees(math.atan2(move_vector[1], move_vector[0]))
                        f[0] += move_vector[0]
                        f[1] += move_vector[1] 
                        f[2] = new_rotation

                    #send
                    self.socket.sendall(json.dumps(self.fish).encode('utf-8'))
                    print(f"POSCLIENT: Sent {json.dumps(self.fish)}")
                    
                    #wait
                    time.sleep(0.5)

                except:
                    print("POSCLIENT: Socket error!")
                    self.socket.close()
                    break
                
        finally:
            print('POSCLIENT: Closing socket')
            self.socket.close()

if __name__ == '__main__':
    try:
        c = TCPDummyClient()
        thread = threading.Thread(target = c.run_thread)
        thread.daemon = True
        thread.start()
        # thread.join()
        while thread.is_alive(): 
            thread.join(1)  # not sure if there is an appreciable cost to this.

    except (KeyboardInterrupt, SystemExit):
        print('\n! Received keyboard interrupt, quitting threads.\n')
        sys.exit()


