"""
Script for labeling box coordinates of finger tips from image directory.
Assumes images in directory are saved as '[integer].jpg'

- Nick
"""

import cv2
import numpy as np
import csv
import os
from random import uniform

IMAGE_SAVE_PATH = 'D:/PCImages/'
CSV_SAVE_PATH = IMAGE_SAVE_PATH

os.chdir(IMAGE_SAVE_PATH)

drawing = False
box_exists = False # True if box was already drawn on current image. This way we avoid multiple labels in same data img
x1 = 0
x2 = 0
y1 = 0
y2 = 0

# TODO: iffy implementation.
try:
    start_file = open('start.txt', 'r')
    start = int(start_file.readline())
    start_file.close()
    print("Restarting labeling from image: " + str(start))
except (TypeError, FileNotFoundError) as e:
    print("NOTE: No previous information found. Will assume this is the first time labeling this data.")
    start = 0

# load pre-existing csv files if labeling data was already started
if start > 0:
    train_csvfile = open(CSV_SAVE_PATH + 'train.csv', 'a') # don't overwrite pre-existing saved data
    validation_csvfile = open(CSV_SAVE_PATH + 'validation.csv', 'a')
    test_csvfile = open(CSV_SAVE_PATH + 'test.csv', 'a')
else:
    train_csvfile = open(CSV_SAVE_PATH + 'train.csv', 'w')
    validation_csvfile = open(CSV_SAVE_PATH + 'validation.csv', 'w')
    test_csvfile = open(CSV_SAVE_PATH + 'test.csv', 'w')

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

# (x2, y2) should be greater than (x1, y1), so if a box is drawn right-to-left, or bottom-to-top, coords are swapped
def redefine_coordinates(x1, y1, x2, y2):
    x1, x2 = swap(x1,x2)
    y1, y2 = swap(y1,y2)
    return x1, y1, x2, y2

# writes data to csv file
def writeLine(csvfile, image_path, x1, y1, x2, y2):
    if x1 == x2 or y1 == y2:
        coord_str = ',,,,0\n'
    else:
        coord_str = str(x1) + ',' + str(y1) + ',' + str(x2) + ',' + str(y2) + ',1\n'
    csvfile.write(image_path + ',' + coord_str)

def draw_box(event, x, y, flags, param):
    global image, drawing, x1, y1, x2, y2, box_exists, csvfile
    if event == cv2.EVENT_LBUTTONDOWN and not box_exists: # button pressed (drawing started)
        x1,y1 = x,y
        drawing=True
    if drawing and event == cv2.EVENT_LBUTTONUP and not box_exists: # button released (drawing ended, box created)
        x2,y2 = x,y
        x1,y1,x2,y2 = redefine_coordinates(x1, y1, x2, y2)
        #print(str((x1,y1,x2,y2)))
        cv2.rectangle(image, (x1,y1), (x2,y2), (0,255,0),2)
        cv2.imshow('', image)
        drawing = False
        box_exists = True

def label_image():
    global box_exists, image, start, x1, y1, x2, y2, which_file
    clone = image.copy() # save copy of image in case need to re-draw box
    while True:
        cv2.imshow('', image)
        cv2.setMouseCallback('', draw_box)
        key = cv2.waitKey(1)
        if key == 8: # backspace, delete box
            image = clone.copy()
            reset_coords()
            box_exists = False
        if key == 13: # enter, save box and data
            # (weighted) random selection of which csv file to save to
            if which_file < 0.7:
                curr_csvfile = train_csvfile
                s = "train"
            elif which_file < 0.9:
                curr_csvfile = validation_csvfile
                s = "validate"
            else:
                curr_csvfile = test_csvfile
                s = "test"
            print("writing " + str(start) + " to " + s)
            writeLine(curr_csvfile, IMAGE_SAVE_PATH + str(start) + '.jpg', x1, y1, x2, y2)
            start += 1
            reset_coords()
            box_exists = False
            which_file = uniform(0.0, 1.0)
            break

which_file = uniform(0.0, 1.0)

# TODO: two different waitKeys, in different nested while loops. Ugly and bad. Still works for now though.
while True:
    image = cv2.imread(str(start) + '.jpg')
    if image is None or cv2.waitKey(0) == 27: # esc
        train_csvfile.close()
        validation_csvfile.close()
        test_csvfile.close()
        break
    label_image()

# checkpoint saving...
start_file = open('start.txt', 'w')
start_file.write(str(start))
start_file.close()
