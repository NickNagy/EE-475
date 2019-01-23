import cv2
import numpy as np
import csv
import os

IMAGE_SAVE_PATH = 'D:/ArduinoImages/'
CSV_SAVE_PATH = IMAGE_SAVE_PATH

os.chdir(IMAGE_SAVE_PATH)

drawing = False
box_exists = False
x1 = 0
x2 = 0
y1 = 0
y2 = 0

csvfile = open(CSV_SAVE_PATH + 'data.csv', 'w')

def reset_coords():
    global x1, y1, x2, y2
    x1 = 0
    x2 = 0
    y1 = 0
    y2 = 0

def swap(val1, val2):
    if val1 > val2:
        temp = val1
        val1 = val2
        val2 = temp
    return val1, val2

def redefine_coordinates(x1, y1, x2, y2):
    x1, x2 = swap(x1,x2)
    y1, y2 = swap(y1,y2)
    return x1, y1, x2, y2

# x1, y1, x2, y2
def writeLine(csvfile, image_path, x1, y1, x2, y2):
    if x1 == x2 or y1 == y2:
        coord_str = ',,,,\n'
    else:
        coord_str = str(x1) + ',' + str(y1) + ',' + str(x2) + ',' + str(y2) + ', finger\n'
    csvfile.write(image_path + ',' + coord_str)

def draw_box(event, x, y, flags, param):
    global image, drawing, x1, y1, x2, y2, box_exists, counter, csvfile
    if event == cv2.EVENT_LBUTTONDOWN and not box_exists:
        x1,y1 = x,y
        drawing=True
    if drawing and event == cv2.EVENT_LBUTTONUP and not box_exists:
        x2,y2 = x,y
        x1,y1,x2,y2 = redefine_coordinates(x1, y1, x2, y2)
        print(str((x1,y1,x2,y2)))
        cv2.rectangle(image, (x1,y1), (x2,y2), (0,255,0),2)
        cv2.imshow('', image)
        drawing = False
        box_exists = True

def label_image():
    global box_exists, image, counter, x1, y1, x2, y2
    clone = image.copy() # save copy of image in case need to re-draw box
    while True:
        cv2.imshow('', image)
        cv2.setMouseCallback('', draw_box)
        if cv2.waitKey(1) == 8: # backspace
            image = clone.copy()
            reset_coords()
            box_exists = False
        if cv2.waitKey(1) == 13: # enter
            print("writing " + str(counter) + " to csv...")
            writeLine(csvfile, IMAGE_SAVE_PATH + str(counter) + '.png', x1, y1, x2, y2)
            counter += 1
            reset_coords()
            box_exists = False
            break


counter = 0

# assumes data is saved as [integer].jpg
while True:
    image = cv2.imread(str(counter) + '.png')
    if image is None:
        csvfile.close()
        break
    label_image()