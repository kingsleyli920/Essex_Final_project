# import packages
import cv2
import time
import numpy as np

# initialize the list of reference points
# and boolean indicating whether cropping is being performed or not
refPt = []
cropping = False
sel_rect_endpoint = []
roi = []
width = 480
height = 320
# mouse events
def click_and_crop(event, x, y, flags, param):
    # get global variables
    global refPt, cropping, sel_rect_endpoint

    # left mouse button click event
    if event == cv2.EVENT_LBUTTONDOWN:
        refPt = [(x, y)]
        cropping = True
    # mouse move event
    elif event == cv2.EVENT_MOUSEMOVE and cropping:
        sel_rect_endpoint = [(x, y)]
    # mouse up event
    elif event == cv2.EVENT_LBUTTONUP:
        # record the end coordinates and indicate cropping is finished
        refPt.append((x, y))
        cropping = False
        
# initialize camera
def init_camera():
    camera = cv2.VideoCapture(0)

    # if no camera, open it
    if not camera.isOpened():
        camera.open()
    else:
        camera.set(3, width)
        camera.set(4, height)
    return camera

def template_match(image, template):

    # convert template to grayscale and get the edge
    template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    template = cv2.Canny(template, 50, 200)
    (tH, tW) = template.shape[:2]
    # cv2.imshow("image1", template)

    # convert whole image to grayscale and get the edge
    # and initialize the bookkeeping variable to keep track of the
    # matched region
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    found = None
    edged = cv2.Canny(gray, 50, 200)
    # cv2.imshow("image2", edged)
    result = cv2.matchTemplate(edged, template, cv2.TM_CCOEFF)
    (_, maxVal, _, maxLoc) = cv2.minMaxLoc(result)

    # draw a bounding box around the detected region
    clone = np.dstack([edged, edged, edged])
    cv2.rectangle(clone, (maxLoc[0], maxLoc[1]),
                  (maxLoc[0] + tW, maxLoc[1] + tH), (0, 0, 255),3)
    # cv2.imshow("image3", clone)

    # if we have found a new maximum correlation value,
    # update the bookkeeping variable
    if found is None or maxVal > found[0]:
        found = (maxVal, maxLoc)

    # unpack the bookkeeping variable and conpute the (x, y) corrdinates
    # of the bounding box
    (_, maxLoc) = found
    (startX, startY) = (int(maxLoc[0]), int(maxLoc[1]))
    (endX, endY) = (int(maxLoc[0] + tW), int(maxLoc[1] + tH))

    # draw a bounding box atound the dectected result and display the image
    cv2.rectangle(image, (startX, startY), (endX, endY), (0, 255, 0),3)
    cv2.imshow("track_image", image)
    
def loop(camera):
    # start loop
    global refPt, cropping, sel_rect_endpoint, roi
    while True:

        # read frames
        if not cropping:
            ret, image = camera.read()

        #
        if not ret:
            break

        # copy frame
        clone = image.copy()

        # name the window
        cv2.namedWindow("image")

        # set mouse event
        cv2.setMouseCallback("image", click_and_crop)

        # show frames and wait for keypress
        if not cropping and refPt == []:
            cv2.imshow("image", image)
            
        elif cropping and sel_rect_endpoint:
            rect_cpy = image.copy()
            cv2.rectangle(rect_cpy, refPt[0], sel_rect_endpoint[0], (0, 0, 255), 3)
            cv2.imshow("image", rect_cpy)
            
        key = cv2.waitKey(1) & 0xFF

        # if r key is pressed, reset the cropping region
        if key == ord("r"):
            image = clone.copy()

        # if c is pressed, break
        elif key == ord("c"):
            break

        # if there are two reference points, crop the region and display
        if len(refPt) == 2:

            # draw a rectangle around the region of interest
            roi = clone[refPt[0][1]:refPt[1][1], refPt[0][0]:refPt[1][0]]
            refPt = []
            sel_rect_endpoint = []
            # cv2.imshow("ROI", roi)
            
        # if have roi
        if roi != []:
            template_match(image, roi)

def cleanup(camera):
    # release camera and close all windows
    camera.release()
    cv2.destroyAllWindows()
    
# main method
def main():

    camera = init_camera()
    loop(camera)
    cleanup(camera)

if __name__ == "__main__":
    main()

