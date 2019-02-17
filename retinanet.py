# -*- coding: utf-8 -*-
"""
Created on Wed Jan 23 17:08:39 2019

@author: Nick Nagy
"""

import tensorflow as tf
import numpy as np
from backboneNetworks import vgg, resnet
from layers import weight, conv2d, pyramid
from collections import OrderedDict

box_ratios = [(0.8, 0.8), (0.9, 0.7), (1.0, 0.6), (0.6, 1.0), (0.7, 9.0)]
areas = [32, 64, 128, 256, 512]
strides = [4, 4, 4, 4, 4]

# TODO: add dropout(?)
def fpn(x, backbone="vgg", backbone_layers=16):
    if backbone == "vgg":
        _, _, _, backboneConvsDict = vgg(x, trainable=False)  # TODO: assure this loads a previously-trained model
    elif backbone == "resnet":
        _, _, convs, backboneConvsDict = resnet(x, trainable=False)  # not yet implemented
    pyramids = OrderedDict()
    pre_pool_convs = [conv for conv in backboneConvsDict if '_3' in backboneConvsDict.keys()]
    # ignore first conv
    pre_pool_convs = pre_pool_convs[1:]
    convs = []
    weights = []
    biases = []
    out_features = 1  # ??
    stddev = np.sqrt(2 / (9 * out_features))
    for i in range(min(5, int(len(pre_pool_convs) / 2))):
        W = weight([3, 3, pre_pool_convs[i].shape[3], out_features], stddev)
        weights.append(W)
        b = bias([out_features])
        biases.append(b)
        convs.append(conv2d(pre_pool_convs[i], W, b))  # add dropout, add relu?
    num_pyramids = len(convs) - 1
    for j in range(num_pyramids):
        conv1 = convs[j]
        conv2 = convs[j + 1]
        name = 'P' + str(j + 3)
        p = pyramid(conv1, conv2, name=name)
        pyramids[name] = p
    return pyramids


# TODO: somewhere put a check to drop any anchor boxes that go beyond pyramid borders

def create_grid_space_boxes(grid_x, grid_y, grid_size, box_ratios):
    grid_space_boxes = np.array((len(box_ratios), 4), dtype=int)
    for i in range(len(box_ratios)):
        w, h = box_ratios[i]
        assert w * h <= 1.0
        w *= grid_size
        h *= grid_size
        centerpoint = (int((grid_x + grid_size) / 2), int((grid_y + grid_size) / 2))
        grid_space_boxes[i][0] = centerpoint[0] - int(w / 2)
        grid_space_boxes[i][1] = centerpoint[1] - int(h / 2)
        grid_space_boxes[i][2] = centerpoint[0] + int(w / 2)
        grid_space_boxes[i][3] = centerpoint[1] + int(h / 2)
    return grid_space_boxes


# assumes pyramids are square
def init_pyramid_boxes(pyramid, area, stride, init_size=244):
    global box_ratios
    pyramid_size = pyramid.shape[0]
    converted_box_size = int(area * pyramid_size / init_size)
    strides_per_row = int((pyramid_size - converted_box_size) / stride) + 1
    for i in range(strides_per_row):
        for j in range(strides_per_row):
            if not (i or j):
                pyramid_boxes = create_grid_space_boxes(0, 0, converted_box_size, box_ratios)
            else:
                pyramid_boxes = np.concatenate(
                    (pyramid_boxes, create_grid_space_boxes(stride * i, stride * j, converted_box_size, box_ratios)))
    corrected_boxes = pyramid_boxes * int(init_size / layer_size)
    return pyramid_boxes, corrected_boxes


# assumptions:
# P3 = 1/2 size of input x (122x122)
# P4 = (61x61)
# P5 = (30x30)
# P6 = (15x15)
# P7 = (7x7)
def init_anchor_boxes(pyramids):
    for i, key in enumerate(pyramids.keys()):
        pyramid_boxes, corrected_boxes = init_pyramid_boxes(pyramids[key], areas[i], strides[i])
        pyramids[key].append(pyramid_boxes)
        if not i:
            all_anchor_boxes = corrected_boxes
        else:
            all_anchor_boxes = np.concatenate(all_anchor_boxes, corrected_boxes)
    return pyramids, all_anchor_boxes
