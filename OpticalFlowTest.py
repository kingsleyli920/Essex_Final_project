import numpy as np
import cv2

rect = (0, 0, 0, 0)
startPoint = False
endPoint = False
midPoint = []
npMidPoint = np.empty([1, 2], dtype=np.float32)
old_gray = None
frame_gray = None

# params for lucas kanade optical flow
lk_params = dict(winSize = (15, 15),
                 maxLevel = 2,
                 criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

def onMouse(event, x, y, flags, params):
    global rect, startPoint, endPoint, midPoint

    # get mouse click
    if event == cv2.EVENT_LBUTTONDOWN:
        if startPoint == True and endPoint == True:
            startPoint = False
            endPoint = False
            rect = (0, 0, 0, 0)

        if startPoint == False:
            rect = (x, y, 0, 0)
            startPoint = True
    if event == cv2.EVENT_MOUSEMOVE:
        if endPoint == False:
            rect = (rect[0], rect[1], x, y)
    if event == cv2.EVENT_LBUTTONUP:
        if endPoint == False:
            endPoint = True
    

camera = cv2.VideoCapture(0)
waitTime = 50

while(camera.isOpened()):

    ret, frame = camera.read()
    if not ret:
        break
    
    cv2.namedWindow('frame')
    cv2.setMouseCallback('frame', onMouse)
    cv2.rectangle(frame, (rect[0], rect[1]), (rect[2], rect[3]), (255, 0, 255), 2)
    
    if startPoint == True and endPoint == True:
        midPoint = [abs(rect[2] - rect[0]) / 2, abs(rect[3] - rect[1]) / 2]
        npMidPoint[0] = midPoint
        

    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    if old_gray == None and midPoint != []:
        old_gray = frame_gray.copy()
        
    if old_gray != None and frame_gray != None:
        # calculate optical flow
        newPoint, status, error = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, npMidPoint, None, **lk_params)
        print("new middle point:", newPoint)
        
   
    
    
    
    

    key = cv2.waitKey(waitTime)

    if key == 27:
        break
    
    if frame_gray != None and midPoint != []:
        old_gray = frame_gray.copy()
camera.release()
cv2.destroyAllWindows()
