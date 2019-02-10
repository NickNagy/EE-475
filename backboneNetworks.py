"""
Some (hopefully) easy-to-incorporate backbone models for our Retinanet project
- Nick
"""

import tensorflow as tf
import numpy as np
from collections import OrderedDict
from layers import weight, bias, conv2d, residual, dense

# from: https://github.com/jakeret/tf_unet/tree/master/tf_unet
def get_image_summary(img):
    V = tf.slice(img, (0, 0, 0, 0), (1,-1,-1,1))
    V -= tf.reduce_min(V)
    V /= tf.reduce_max(V)
    V *= 255
    img_w = tf.shape(img)[1]
    img_h = tf.shape(img)[2]
    V = tf.reshape(V, tf.stack((img_w, img_h, 1)))
    V = tf.transpose(V, (2,0,1))
    V = tf.reshape(V, tf.stack((-1, img_w, img_h, 1)))
    return V

# to handle a VGG16 model or a VGG19 model
def vgg(x, dropout, num_classes=2, kernel_size=3, num_layers=16, summaries=True):
    assert num_layers == 16 or num_layers == 19 # for now

    w = x.shape[1]  # should be 224x224
    h = x.shape[2]

    size = 224#w
    stddev = np.sqrt(2 / (kernel_size * kernel_size))

    weights = []
    biases = []
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
                b = bias([out_features])
                weights.append(W)
                biases.append(b)
                conv = tf.nn.relu(conv2d(curr_input, W, b, dropout))
                convs.append(conv)
                convsDict[str(size) + '_' + str(layer)] = conv
                curr_input = conv
                in_features = out_features
        # pool
        pool_layer = tf.nn.max_pool(curr_input, [1, 2, 2, 1], [1, 2, 2, 1], padding='VALID')
        curr_input = pool_layer
        out_features = min(512, out_features*2)
        size = int(size/2)

    if summaries:
        with tf.name_scope("summaries"):
            #for i in range(len(convs)):
            #    tf.summary.image()
            for k in convsDict.keys():
                tf.summary.image("conv_" + k, get_image_summary(convsDict[k]))

    # TODO: add dropout
    flat_dimension = 4608 #7*7*512

    flatten = tf.reshape(curr_input, [-1, flat_dimension])#tf.layers.Flatten()(curr_input)

    stddev = np.sqrt(2/flat_dimension)
    in_features = flat_dimension
    out_features = 4096
    W = weight([in_features, out_features], stddev)
    b = bias([out_features])
    weights.append(W)
    biases.append(b)
    dense1 = dense(flatten, W, b, dropout)#dense(flatten, units=4096)

    in_features = out_features

    stddev = np.sqrt(2/out_features)
    W = weight([in_features, out_features], stddev)
    b = bias([out_features])
    weights.append(W)
    biases.append(b)
    dense2 = dense(dense1, W, b, dropout)#dense(dense1, units=4096)

    W = weight([in_features, num_classes], stddev)
    b = bias([num_classes])
    weights.append(W)
    biases.append(b)
    logits = dense(dense2, W, b, dropout)#dense(dense2, units=num_classes)

    # return convsDict for retinaNet

    variables = []
    for w in weights:
        variables.append(w)
    for b in biases:
        variables.append(b)

    return logits, variables, convs, convsDict

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
    
