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


def pyramid_layer(conv1, conv2):
    convs = []
    weights = []
    biases = []
    out_features = 256
    stddev = np.sqrt(2 / out_features)
    W1 = weight([1, 1, conv1.shape[3], out_features], stddev)
    b1 = bias([out_features])
    W2 = weight([1, 1, conv2.shape[3], out_features], stddev)
    b2 = bias([out_features])
    # RELU?
    conv1 = conv2d(conv1, W1, b1)  # tf.nn.relu(conv2d())
    conv2 = conv2d(conv2, W2, b2)
    convs.append(conv1)
    convs.append(conv2)
    conv2_upsample = tf.image.resize_images(image=conv2, size=(2 * conv2.shape[1], 2 * conv2.shape[2]),
                                            method=ResizeMethod.NEAREST_NEIGHBOR)
    conv1_plus_conv2 = tf.add(conv1, conv2_upsample)
    W = weight([3, 3, out_features, out_features], stddev)
    b = bias([out_features])
    # RELU?
    pyramid = conv2d(conv1_plus_conv2, W, b)
    weights.append(W)
    biases.append(b)
    return pyramid, convs, weights, biases


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
    # TODO: name the conv layers
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
        p, p_convs, p_weights, p_biases = pyramid_layer(conv1, conv2)
        pyramids[name] = p
        convs += p_convs
        weights += p_weights
        biases += p_biases
    return pyramids, convs, weights, biases


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
def init_pyramid_anchor_boxes(pyramid, area, stride, init_size=244):
    global box_ratios
    pyramid_size = pyramid.shape[0]
    converted_box_size = int(area * pyramid_size / init_size)
    stride = converted_box_size
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
        pyramid_boxes, corrected_boxes = init_pyramid_anchor_boxes(pyramids[key], areas[i], strides[i])
        pyramids[key].append(corrected_boxes)  # pyramid_boxes)
        if not i:
            all_anchor_boxes = corrected_boxes
        else:
            all_anchor_boxes = np.concatenate(all_anchor_boxes, corrected_boxes)
    return pyramids, all_anchor_boxes


def regression_head(pyramid_layer, pyramid_boxes):
    num_boxes = pyramid_boxes.shape[0]
    convs = []
    weights = []
    biases = []
    out_features = 256
    curr_node = pyramid_layer
    stddev = np.sqrt(2 / (9 * out_features))
    for i in range(3):
        W = weight([3, 3, curr_node.shape[3], out_features], stddev)
        b = bias([out_features])
        conv = conv2d(curr_node, W, b)
        convs.append(tf.nn.relu(conv))
        weights.append(W)
        biases.append(b)
        curr_node = convs[-1]
    out_features = 4 * num_boxes
    stddev = np.sqrt(2 / (9 * out_features))
    W = weight([3, 3, 256, out_features], stddev)
    b = bias([out_features])
    conv = conv2d(curr_node, W, b)
    convs.append(tf.nn.relu(conv))
    curr_node = convs[-1]
    weights.append(W)
    biases.append(b)
    output = tf.nn.sigmoid(curr_node)
    return output, convs, weights, biases


def classification_head(pyramid_layer, pyramid_boxes, num_classes=2):
    num_boxes = pyramid_boxes.shape[0]
    convs = []
    weights = []
    biases = []
    out_features = 256
    curr_node = pyramid_layer
    stddev = np.sqrt(2 / (9 * out_features))
    for i in range(3):
        W = weight([3, 3, curr_node.shape[3], out_features], stddev)
        b = bias([out_features])
        conv = conv2d(curr_node, W, b)
        convs.append(tf.nn.relu(conv))
        weights.append(W)
        biases.append(b)
        curr_node = convs[-1]
    out_features = num_classes * num_boxes
    stddev = np.sqrt(2 / (9 * out_features))
    W = weight([3, 3, 256, out_features], stddev)
    b = bias([out_features])
    conv = conv2d(curr_node, W, b)
    convs.append(tf.nn.relu(conv))
    curr_node = convs[-1]
    weights.append(W)
    biases.append(b)
    output = tf.nn.sigmoid(curr_node)
    return output, convs, weights, biases


# TODO: convsDict? Or a cleaner manner of storing different layer/variable types
def retinanet(x, backbone_model="vgg", backbone_layers=16):
    pyramids, convs, weights, biases = fpn(x, backbone_model, backbone_layers)
    pyramids, all_anchor_boxes = init_anchor_boxes(pyramids)
    stddev = np.sqrt(2 / 9)
    for key in pyramids.keys():
        curr_node = pyramids[key][0]
        pyramid_weights = []
        pyramid_biases = []
        pyramid_variables = []
        W = weight([3, 3, 1, 1], stddev)
        b = bias([1])
        pyramid_weights.append(W)
        pyramid_biases.append(b)
        conv3x3 = conv2d(curr_node, W, b)
        convs.append(tf.nn.relu(conv3x3))
        curr_node = convs[-1]
        regression_output, regression_convs, regression_weights, regression_biases = regression_head(curr_node,
                                                                                                     pyramids[key][1])
        classification_output, classification_convs, classification_weights, classification_biases = classification_head(
            curr_node, pyramids[key][1])
        pyramid_weights = pyramid_weights + regression_weights + classification_weights
        pyramid_biases = pyramid_biases + regression_biases + classification_biases
        for w in pyramid_weights:
            pyramid_variables.append(w)
        for b in pyramid_biases:
            pyramid_variables.append(b)
        pyramid[key].append(pyramid_variables)
        pyramid[key].append(classification_output)
        pyramid[key].append(regression_output)
    shared_variables = []
    for w in weights:
        shared_variables.append(w)
    for b in biases:
        shared_variables.append(b)
    return pyramids, shared_variables
