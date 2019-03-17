import numpy as np
from scipy.misc import imresize
from scipy.ndimage.filters import convolve
from utils import get_max_conf_cell, convert_xywh_to_xyxy, remove_borders
import cv2

VARS_PATH = "C://Users//Nick Nagy//Desktop//Python//Capstone//Variables//"

# TODO: better implementation
pool_layers = {'1':2, '2': 2, '3':2, '4':2}

def load_weight(path, layer):
    return np.load(path + 'weight_' + str(layer))

def load_bias(path, layer):
    return np.load(path + 'bias_' + str(layer))

def load_vars(path):
    idx = 0
    weights_list = []
    biases_list = []
    while True:
        weights_list.append(load_weight(path, idx))
        biases_list.append(load_bias(path, idx))
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
    return np.maximum(input, np.zeros(shape=input.shape))

def model(input, weights, biases, pool_layers):
    curr_node = input
    layer = 0
    while True:
        try:
            curr_node = relu(convolution(curr_node, weights[layer], biases[layer]))
            if layer in pool_layers.keys():
                curr_node = max_pool(curr_node, pool_layers[layer])
            layer += 1
        except:
            break
    return curr_node

def predict(input, weights, biases, pool_layers, num_boxes=2):
    logits = model(input, weights, biases, pool_layers)
    return get_max_conf_cell(logits, num_boxes)

if __name__ == '__main__':
    w,b = load_vars(VARS_PATH)
    cap = cv2.VideoCapture(0)
    while True:
        _, frame = cap.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        prediction = predict(imresize(remove_borders(frame),(224,224)), w, b, pool_layers)