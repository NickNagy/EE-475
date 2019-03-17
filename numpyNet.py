import numpy as np
from scipy.misc import imresize
from scipy.ndimage.filters import convolve
from utils import convert_xywh_to_xyxy, remove_borders
import cv2

VARS_PATH = "C://Users//Nick Nagy//Desktop//Python//Capstone//Variables//"

# TODO: better implementation
pool_layers = {'1':2, '2': 2, '3':2, '4':2}

def load_weight(path, layer):
    return np.load(path + 'weights_' + str(layer) + '.npy')

def load_bias(path, layer):
    return np.load(path + 'biases_' + str(layer) + '.npy')

def load_vars(path):
    print("Loading Variables...")
    idx = 0
    weights_list = []
    biases_list = []
    while True:
        try:
            weights_list.append(load_weight(path, idx))
            biases_list.append(load_bias(path, idx))
            idx += 1
        except:
            break
    return weights_list, biases_list

# TODO: parallel implementation?
def max_pool(input, s):
    dim = int(input.shape[0]/s)
    output = np.zeros(shape=(dim, dim))
    for i in range(dim):
        for j in range(dim):
            output[i,j] = max(input[s*i:s*(i+1), s*j:s*(j+1)])
    return output

def convolution(input, weight, bias):
    return np.add(convolve(input, weight), bias) # default 'reflect'

def relu(input):
    return np.maximum(input, 0)#np.zeros(shape=input.shape))

def model(input, weights, biases, pool_layers):
    curr_node = input
    layer = 0
    while True:
        try:
            print(curr_node.shape)
            curr_node = relu(convolution(curr_node, weights[layer], biases[layer]))
            if layer in pool_layers.keys():
                curr_node = max_pool(curr_node, pool_layers[layer])
            layer += 1
        except:
            break
    return curr_node

def get_max_conf_cell(logits, num_boxes):
    boxes = logits.reshape(-1, num_boxes, 5)
    max_conf_idx_arr = np.argmax(boxes[:,:,4])
    max_conf_box = tf.argmax(max_conf_idx_arr)
    max_conf_cell = max_conf_idx_arr[max_conf_box]
    box = boxes[max_conf_cell, max_conf_box, :]
    return [max_conf_cell, box[0], box[1], box[2], box[3]]

def predict(input, weights, biases, pool_layers, num_boxes=2):
    logits = model(input.reshape(1, input.shape[0], input.shape[1],1), weights, biases, pool_layers)
    return get_max_conf_cell(logits, num_boxes)

if __name__ == '__main__':
    w,b = load_vars(VARS_PATH)
    cap = cv2.VideoCapture(0)
    while True:
        _, frame = cap.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        prediction = predict(imresize(remove_borders(frame),(224,224)), w, b, pool_layers)
        print(prediction)
