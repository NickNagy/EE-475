# -*- coding: utf-8 -*-
"""
Created on Wed Jan 23 17:08:39 2019

@author: Nick Nagy
"""

import tensorflow as tf
import numpy as np
from backboneNetworks import vgg, resnet
from layers import weight, conv2d

box_ratios = [(0.8,0.8),(0.9, 0.7),(1.0,0.6),(0.6,1.0),(0.7,9.0)]

def create_grid_boxes(grid_x, grid_y, grid_size):
    grid_boxes = np.ndarray(shape=(len(boxes),4), dtype=int)
    for i in range(len(boxes)):
        w,h = boxes[i]
        assert w*h <= 1.0
        w *= grid_size
        h *= grid_size
        # want to return the top left and bottom right coordinates wrt grid spot
        centerpoint = (int((grid_x + grid_size)/2), int((grid_y + grid_size)/2))
        top_left = (centerpoint[0]-int(w/2), centerpoint[1]-int(h/2))
        bot_right = (centerpoint[0]+int(w/2), centerpoint[1]+int(h/2))
        grid_boxes[i][0] = top_left[0]
        grid_boxes[i][1] = top_left[1]
        grid_boxes[i][2] = bot_right[0]
        grid_boxes[i][3] = bot_right[1]
    return grid_boxes

def create_image_boxes(image, grid_squares):
    w = image.shape[0]
    grid_size = int(w/sqrt(grid_squares))
    image_boxes = np.ndarray(shape=(len(boxes)*grid_squares, 4), dtype=int)
    i = 0
    for x in range(int(sqrt(grid_squares))):
        for y in range(int(sqrt(grid_squares))):
            image_boxes[i:i+len(boxes)] = create_grid_boxes(2*x*grid_size, 2*y*grid_size, grid_size)
            i += len(boxes)
    return image_boxes

def create_anchors(backbone_convs, base_grid_size=16):
    # backbone_convs: a dictionary of convolutional layers
    anchor_layers = [backbone_convs[layer] for layer in backbone_convs.keys() if '_3' in layer]
    
    for layer, (i) in anchor_layers:
        grid_squares = base_grid_size*i
        w,h = layer.shape[1][2]
        for x in range(w):
            for y in range()
