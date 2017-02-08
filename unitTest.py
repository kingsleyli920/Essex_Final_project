
import cv2
import time
import numpy as np
import BrickPi

Hmin = 42
Hmax = 92
Smin = 62
Smax = 255
Vmin = 63
Vmax = 235

rangeMin = np.array([Hmin, Smin, Vmin], np.uint8)
rangeMax = np.array([Hmax, Smax, Vmax], np.uint8)

minArea = 50

camera = cv2.VideoCapture(0)

width = 240
height = 160
def move_horizontal(area):
    if (area <= 120):
        print("Move forward")
    elif (area >= 600):
        print("Move Backward")
        
        
if camera.isOpened():
    camera.set(3, width)
    camera.set(4, height)
else:
    print("Webcam not open")
    camera.open(0)

while camera.isOpened():
    ret, frame = camera.read()
    imgHSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    imgThresh = cv2.inRange(imgHSV, rangeMin, rangeMax)
    imgErode = cv2.erode(imgThresh, None, iterations = 3)
    imgDilate = cv2.dilate(imgErode, None, iterations = 3)
    cnts = cv2.findContours(imgDilate.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[-2] 
    cv2.drawContours(frame, cnts, -1, (0, 0, 255), 3)
    if len(cnts) > 0:
        c = max(cnts, key = cv2.contourArea)
        cv2.drawContours(frame, c, -1, (0, 0, 255), 3)
    moments = cv2.moments(imgDilate, True)
    area = moments['m00']
    if area >= minArea:
        x = moments['m10'] / area
        y = moments['m01'] / area
        move_horizontal(area)
        #print(x, ", ", y)
        cv2.circle(frame, (int(x), int(y)), 5, (0, 255, 0), -1)
    cv2.imshow("Frame", frame)
    cv2.imshow("HSV", imgHSV)
    cv2.imshow("Thre", imgThresh)
    cv2.imshow("Erosao", imgErode)
    cv2.imshow("Dilate", imgDilate)

    if cv2.waitKey(10) == 27:
        break
camera.release()
cv2.destroyAllWindows()
