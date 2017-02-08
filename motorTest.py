from BrickPi import *

#setup the serial port for communication
BrickPiSetup()
    #enable motors
BrickPi.MotorEnable[PORT_B] = 1
BrickPi.MotorEnable[PORT_C] = 1
    #setup sensors
BrickPiSetupSensors()

while True:
    BrickPi.MotorSpeed[PORT_B] = 255
    BrickPi.MotorSpeed[PORT_C] = 255
    BrickPiUpdateValues()
