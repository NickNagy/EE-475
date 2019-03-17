#from netRunner import predict
import tensorflow as tf
import numpy as np
import cv2
from yoloClasses import YoloNetwork
from utils import convert_xywh_to_xyxy, remove_borders
from scipy.misc import imresize
import win32api, win32con
import msvcrt
import keyboard

# constants
NUM_CELLS = 7
NUM_BOXES = 3
MODEL_PATH = "C://Users//Nick Nagy//Desktop//Python//Capstone"

def init(num_cells=7, num_boxes=2):
    cap = cv2.VideoCapture(0)
    model = YoloNetwork(1, 2, num_cells, num_boxes)
    return cap, model

def restore_model(sess, model, model_path):
    init = tf.variables_initializer(model.variables)
    sess.run(init)
    model.restore(sess, model_path)

def get_prediction_raw(sess, image, model, num_cells=7):
    prediction = sess.run(model.predicter, feed_dict={model.x: image.reshape(1, image.shape[0], image.shape[1], 1),
                                                      model.y: np.empty((1, num_cells, num_cells, 5)),
                                                      model.dropout: 1.0})
    return convert_xywh_to_xyxy(np.asarray(prediction[:5]), num_cells=num_cells)[0]

def get_prediction_converted(coords, output_window=(1920,1080), input_window=(224,224)):
    w = int(output_window[0]/input_window[0])
    h = int(output_window[1]/input_window[1])
    return [coords[0]*w, coords[1]*h, coords[2]*w, coords[3]*h]

def get_centerpoint(coords):
    return coords[2]-coords[0], coords[3]-coords[1]

def click():
    x,y = win32api.GetCursorPos()
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,x,y,0,0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,x,y,0,0)

def set_mouse(x,y):
    win32api.SetCursorPos((x,y))

def non_touch_mouse_movement(sess, cap, model, num_cells=7):
    _, frame = cap.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    raw_coords = get_prediction_raw(sess, imresize(remove_borders(frame), (224, 224)), model, num_cells)
    x,y = get_centerpoint(get_prediction_converted(raw_coords))
    set_mouse(x,y)

if __name__ == '__main__':
    cap, model = init(NUM_CELLS, NUM_BOXES)
    with tf.Session() as sess:
        restore_model(sess, model, MODEL_PATH)
        while True:
            if keyboard.is_pressed('q'):
                break
            non_touch_mouse_movement(sess, cap, model, NUM_CELLS)