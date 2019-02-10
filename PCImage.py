import cv2
import numpy as np
from scipy.misc import imresize

SAVE_PATH = "D:/PCImages/"

cap = cv2.VideoCapture(0)

def remove_borders(frame):
    top = 0
    while np.sum(frame[top,:]) == 0:
        top += 1
    bottom = frame.shape[0]-1
    while np.sum(frame[bottom,:])==0:
        bottom -= 1
    return frame[top:bottom, :]

counter = 0

while True:
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = remove_borders(gray)
    cv2.imshow('frame', gray)
    if cv2.waitKey(1) == ord('q'):
        break
    cv2.imwrite(SAVE_PATH + str(counter) + ".jpg", imresize(gray, (224, 224)))
    counter += 1
