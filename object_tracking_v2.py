# import necessary packages
from collections import deque
from BrickPi import *

import numpy as np
import argparse
import imutils
import cv2
import threading
import time

class myThread (threading.Thread):
    def __init__(self, threadId, name, counter):
        threading.Thread.__init__(self)
        self.threadId = threadId
        self.name = name
        self.counter = counter
    def run(self):
        while True:
            BrickPiUpdateValues()
            time.sleep(.5)

# construct the argument parse and parse arguments
def constructArgParses():
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--video",
                help="path to the (optional) video file")
    ap.add_argument("-b", "--buffer", type=int, default=32,
                help="max buffer size")
    args = vars(ap.parse_args())
    return args
    
def analyseSource(args):
    # if a video path was not supplied, grab the reference to the webcam
    if not args.get("video", False):
        camera = cv2.VideoCapture(0)
    # otherwise, grab a reference to the video file
    else:
        camera = cv2.VideoCapture(args["video"])
    if camera.isOpened():
        return camera
    else:
        camera.open(0)
def setupBrickPi():
    #setup the serial port for communication
    BrickPiSetup()
    #enable motors
    BrickPi.MotorEnable[PORT_B] = 1
    BrickPi.MotorEnable[PORT_C] = 1
    #setup sensors
    BrickPiSetupSensors()
    
def forward():
    BrickPi.MotorSpeed[PORT_C] = 150
    BrickPi.MotorSpeed[PORT_B] = 150
    
def backward():
    BrickPi.MotorSpeed[PORT_C] = -150
    BrickPi.MotorSpeed[PORT_B] = -150
    
def left():
    BrickPi.MotorSpeed[PORT_C] = -150
    BrickPi.MotorSpeed[PORT_B] = 150
    
def right():
    BrickPi.MotorSpeed[PORT_C] = 150
    BrickPi.MotorSpeed[PORT_B] = -150
    
def stop():
    BrickPi.MotorSpeed[PORT_C] = 0
    BrickPi.MotorSpeed[PORT_B] = 0
    
def trackZ(area):
    if area > 1700:
        backward()
    elif area < 500 and area > 0:
        forward()
    else:
        stop()

def trackX(dX):
    if dX < 50 and dX > 0:
        left()
    elif dX > 280:
        right()
    else:
        stop()
        
def processFrames(frame, greenLower, greenUpper):
    # resize the frame, blur it and convert to HSV
    frame = imutils.resize(frame, width=160)
    blurred = cv2.GaussianBlur(frame, (11, 11), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # construct a mask for the color "green", then perform a series
    # of dilations and erosions to remove any small blobs left in the
    # mask
    mask = cv2.inRange(hsv, greenLower, greenUpper)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    return mask

def startLoop(args, camera, greenLower, greenUpper, dX, dY):
    # start loop
    while True:
        # grab the current frame
        ret, frame = camera.read()
        # if view a video and with no frame has been catched,
        # the video has ended.
        if args.get("video") and not ret:
            break
        mask = processFrames(frame, greenLower, greenUpper
                             )
        # find contours in the mask and initialize the current
        # (x, y) center of the ball
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)[-2]

        # only proceed if at least one contour was found
        if len(cnts) > 0:
            # find the largest contour in the mask, then use it to compute the
            # minimum enclosing circle and centroid
            c = max(cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            area = M["m00"]
            (dX, dY) = (int(M["m10"] / area), int(M["m01"] / area))
            center = (dX, dY)
            print("Radius:", radius, "Area:", area)
            print("---------------------------------")
            print("x:", dX, "y:", dY)
            print()
            # only proceed if the radius meets a minimum size
            if radius > 0:
                # draw the circle and centroid on the frame,
                # then update the list of tracked points
                cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                cv2.circle(frame, center, 5, (0, 0, 255), -1)
            trackZ(area)
            
        else:
            dX, dY, area = -1, -1, -1
        # show the frame to our screen and increment the frame counter
        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF

        # if the 'q' key is pressed, stop the loop
        if key == ord("q"):
            break
def cleanup(camera):
    # cleanup the camera and close all windows
    camera.release()
    cv2.destroyAllWindows()

def main():
    
    args = constructArgParses()
    
    # define the lower and upper boundaries of the "green" ball in HSV color space
    greenLower = (42, 62, 63)
    greenUpper = (92, 255, 235)
    dX = ""
    dY = ""
    
    camera = analyseSource(args)
    setupBrickPi()
    
    thread = myThread(1, "myThread", 1)
    thread.setDaemon(True)
    thread.start()
    startLoop(args, camera, greenLower, greenUpper, dX, dY)
    cleanup(camera)
    
if __name__ == "__main__":
    main()
















        






















    
