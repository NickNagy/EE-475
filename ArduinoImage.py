import serial, time
import cv2
import numpy as np
from sys import stdout
from scipy.misc import imresize

# paths
IMG_SAVE_PATH = 'D:/ArduinoImages'
CSV_SAVE_PATH = IMG_SAVE_PATH

# constants for serial connection
PORT = 'COM7'
BAUD_RATE = 921600

# mode should be 'IDLE', 'REAL-TIME', or 'SAVE'
# 'IDLE': display images, but don't save
# 'REAL-TIME': save images, and write box coordinates & image path to csv file
# 'SAVE': save images, but don't write coordinate data
# WARNING: 'REAL-TIME' mode assumes that a finger class is always present in captures!
MODE = 'SAVE'

# image dimensions
WIDTH = 320 >> 1
HEIGHT = 240 >> 1

def writeLine(csvfile, path, coordinates):
    csvfile.write(path + ',' + str(coordinates[0]) + ',' + str(coordinates[1]) + ',' + str(coordinates[2]) + ',' + str(
        coordinates[3]) + ', finger' + '\n')

csvfile = open(CSV_SAVE_PATH + '/data.csv', 'w')
ser = serial.Serial(PORT, BAUD_RATE, timeout=2)

arr = np.zeros(shape=(HEIGHT, WIDTH)).astype('uint8')  # no valid data yet

# when initialized, camera first sends an ACK statement
skip_ack = stdout.write(ser.readline().decode())
time.sleep(0.3)

ser.write(bytearray([1]))  # request capture
counter = 0
box_coordinates = [0, 0, 0, 0]  # TODO

while True:
    try:
        # load each transmitted pixel to appropriate spot in arr
        for i in range(0, HEIGHT):
            for j in range(0, WIDTH):
                arr[i, j] = ord(ser.read())  # unicode to int

        ser.write(bytearray([1])) # prep next capture

        cv2.imshow('', arr)
        # end display if spacebar is pressed
        if cv2.waitKey(1) == 27:
            break

        # evaluate mode for saving type
        if MODE is not 'IDLE':
            cv2.imwrite(IMG_SAVE_PATH + '/' + str(counter) + '.jpg', imresize(arr, (224,224)))  # saves capture to IMG_SAVE_PATH
            if MODE is 'REAL-TIME':
                writeLine(csvfile, IMG_SAVE_PATH + '/' + str(counter) + '.jpg', imresize(box_coordinates, (224,224)))

        counter += 1
    except TypeError:
        stdout.write('error')
        ser.write(bytearray([1]))

ser.write(bytearray([0]))
csvfile.close()
