import cv2
from scipy.misc import imresize

SAVE_PATH = "D:/PCImages/"

cap = cv2.VideoCapture(0)

counter = 0
while True:
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cv2.imshow('frame', gray)
    if cv2.waitKey(1) == 27:
        break
    cv2.imwrite(SAVE_PATH + str(counter) + ".jpg", imresize(gray, (224, 224)))
    counter += 1
