from socket import *
from BrickPi import *

import time
import threading
import select
import queue
from threading import Thread
import sys

#setup the serial port for communication
BrickPiSetup()
#enable motors
BrickPi.MotorEnable[PORT_B] = 1
BrickPi.MotorEnable[PORT_C] = 1
#setup sensors
BrickPiSetupSensors()
#get ip address
def get_local_address():
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect(('google.com', 0))
    ipaddr = s.getsockname()[0]
    s.close()
    return ipaddr
#pi host and port
HOST = get_local_address()
#print(HOST)
PORT = 9876
#create serversocket
running = True



#motor running thread
class BrickPiThread(threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter

    def run(self):
        while running:
            BrickPiUpdateValues()

brickPiThread = BrickPiThread(1, "BrickPiThread", 1)
brickPiThread.Daemon = True
brickPiThread.start()
    

#main thread to process command from client
class ProcessCommandThread(Thread):
    def __init__(self):
        super(ProcessCommandThread, self).__init__()
        self.running = True
        self.q = queue.Queue()

    def add(self, cmd):
        #print("Add cmd:", cmd)
        self.q.put(cmd)
        #print("Put cmd:", self.q.get)

    def stop(self):
        self.running = False

    def run(self):
        q = self.q
        while self.running:
            try:
                cmd = q.get(block=True, timeout=1)
                process(cmd)
            except queue.Empty:
                sys.stdout.write('.')
                sys.stdout.flush()
        if not q.empty():
            print("Elements left in queue:")
            while not q.empty():
                print(q.get)

commandThread = ProcessCommandThread()
commandThread.start()

def process(cmd):
    print("Processing [{v}]".format(v=cmd))

    if cmd == b'CONNECT':
        print("CONNECT")
    elif cmd == b'DISCONNECT':
        print("DISCONNECT")
    elif cmd == b'LEFT-FWD-START':
        BrickPi.MotorSpeed[PORT_C] = 255
    elif cmd == b'LEFT-FWD-STOP':
        BrickPi.MotorSpeed[PORT_C] = 0
    elif cmd == b'LEFT-BWD-START':
        BrickPi.MotorSpeed[PORT_C] = -255
    elif cmd == b'LEFT-BWD-STOP':
        BrickPi.MotorSpeed[PORT_C] = 0
    elif cmd == b'RIGHT-FWD-START':
        BrickPi.MotorSpeed[PORT_B] = 255
    elif cmd == b'RIGHT-FWD-STOP':
        BrickPi.MotorSpeed[PORT_B] = 0
    elif cmd == b'RIGHT-BWD-START':
        BrickPi.MotorSpeed[PORT_B] = -255
    elif cmd == b'RIGHT-BWD-STOP':
        BrickPi.MotorSpeed[PORT_B] = 0

def main():

    serversocket = socket(AF_INET, SOCK_STREAM)
    serversocket.bind((HOST, PORT))
    serversocket.listen(1)
    (clientsocket, address) = serversocket.accept()
    while True:
        
        ready = select.select([clientsocket, ], [], [], 1)
        if ready[0]:
            cmd = clientsocket.recv(4096)
        if cmd == b'':
            break
        else:
            commandThread.add(cmd)
                 
    cleanup()

def cleanup():
    commandThread.stop()
    commandThread.join()

if __name__ == "__main__":
    main()
    
