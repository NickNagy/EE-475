"""
Some (hopefully) easy-to-incorporate backbone models for our Retinanet project
- Nick
"""

import tensorflow as tf
import numpy as np
from collections import OrderedDict
from layers import weight, conv2d, residual, dense

# to handle a VGG16 model or a VGG19 model
def vgg(x, num_classes=2, kernel_size=3, num_layers=16):
    assert num_layers == 16 or num_layers == 19 # for now

    w = x.shape[1]  # should be 224x224
    h = x.shape[2]

    size = 224#w
    stddev = np.sqrt(2 / (kernel_size * kernel_size))

    weights = []
    convs = []
    convsDict = OrderedDict()

    out_features = 64
    curr_input = x

    # conv layers
    while size > 7:
        stddev = np.sqrt(2 / (kernel_size * kernel_size * out_features))
        if size == 224 or size == 112:
            size_layers = 2
        else:
            if num_layers == 16:
                size_layers = 3
            else:
                size_layers = 4
        for layer in range(size_layers):
            if layer == 0:
                if size == 224:
                    in_features = 1
                elif in_features != 512: # once in_features = 512, don't want to divide it
                    in_features = int(out_features / 2)
            else:
                #in_features = out_features
                W = weight([kernel_size, kernel_size, in_features, out_features], stddev)
                weights.append(W)
                conv = tf.nn.relu(conv2d(curr_input, W))
                convs.append(conv)
                convsDict[str(size) + '_' + str(layer)] = conv
                curr_input = conv
                in_features = out_features
        # pool
        pool_layer = tf.nn.max_pool(curr_input, [1, 2, 2, 1], [1, 2, 2, 1], padding='VALID')
        curr_input = pool_layer
        out_features = min(512, out_features*2)
        size /= 2

    # TODO: add dropout
    flatten = tf.layers.Flatten()(curr_input)
    dense1 = dense(flatten, units=4096)
    dense2 = dense(dense1, units=4096)
    logits = dense(dense2, units=num_classes)

    # return convsDict for retinaNet
    return logits, weights, convs, convsDict

def resnet(x, num_classes=1, num_layers=34, custom_pattern=[]):
    w, h = x.shape

    size = w

    convs = []
    weights = []
    convsDict = OrderedDict()

    # TODO: expand for num_layers > 34
    if num_layers == 18:
        pattern = {'112': 4, '': 4, '28': 4, '14': 4}
    elif num_layers == 34:
        pattern = {'112': 6, '56': 8, '28': 8, '14': 6}
    else:
        assert num_layers % 2 == 0
        if custom_layers is not None:
            assert sum(custom_layers) == num_layers - 2
            pattern = {'112': custom_layers[0], '56': custom_layers[1], '28': custom_layers[2], '14': custom_layers[3]}

    out_features = 64
    curr_input = x

    kernel_size = 7
    stride_width = 2
    is_residual_step = True

    # conv layers
    while size > 7:
        stddev = np.sqrt(2 / (kernel_size * kernel_size * out_features))
        if size == 224:
            in_features = 1
            W = weight([in_features, kernel_size, kernel_size, out_features], stddev)
            weights.append(W)
            conv = tf.nn.relu(conv2d(curr_input, W, strides=[1, stride_width, stride_width, 1], padding='VALID'))
            convs.append(conv)
            convsDict['0'] = conv
            pool_layer = tf.nn.max_pool(conv, [1, 2, 2, 1], padding='VALID')
            curr_input = pool_layer
            size /= 2
            kernel_size = 3
            in_features = 64
            stride_width = 1
        else:
            for layer in range(pattern[str(size)]):
                W = weight([in_features, kernel_size, kernel_size, out_features], stddev)
                weights.append(W)
                conv = tf.nn.relu(conv2d(curr_input, W, strides=[1, stride_width, stride_width, 1], padding='VALID'))
                is_residual_step = not is_residual_step
                curr_input = conv
                convs.append(conv)
                convsDict[str(size) + '_' + str(layer)] = conv
                if is_residual_step:
                    curr_input = residual(conv, convs[-2])
                if layer == pattern[str(size)] - 1:
                    stride_width = 2
                    size /= 2
                    out_features *= 2
                else:
                    stride_width = 1
                    in_features = out_features

    # TODO: fc layer
    output = None

    return output, weights, convs, convsDict
    
    
