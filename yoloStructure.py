import tensorflow as tf
import numpy as np
from collections import OrderedDict
from layers import weight, bias, conv2d, residual, dense, pool
from utils import get_image_summary, IoU


def conv_step(convs, weights, biases, x, k, s, in_features, out_features, dropout):
    stddev = np.sqrt(2 / in_features)
    W = weight([k, k, in_features, out_features], stddev)
    b = bias([out_features])
    curr_node = tf.nn.leaky_relu(conv2d(x, W, b, dropout, stride=s))
    convs.append(curr_node)
    weights.append(W)
    biases.append(b)
    return convs, weights, biases, curr_node


def yolo(x, dropout=0.5, num_classes=2, num_channels=1, summaries=True, num_boxes=2, num_cells=7):
    size = 224

    in_features = num_channels
    out_features = 64

    with tf.name_scope("preprocessing"):
        w = tf.shape(x)[1]  # should be 224x224
        h = tf.shape(x)[2]
        x = tf.cast(tf.reshape(x, tf.stack([-1, w, h, 1])), tf.float32)

    curr_node = x

    weights = []
    biases = []
    convs = []
    convsDict = OrderedDict()

    # Conv 1
    convs, weights, biases, curr_node = conv_step(convs, weights, biases, curr_node, 7, 2, in_features, out_features, dropout)
    size = int(size/2) #112
    in_features = out_features

    # Max pool 1
    #curr_node = pool(curr_node, 2, 2)
    #size = int(size/2) #56

    # Conv 2
    out_features = 192
    convs, weights, biases, curr_node = conv_step(convs, weights, biases, curr_node, 3, 1, in_features, out_features,
                                                  dropout)
    in_features = out_features

    # Max pool 2
    curr_node = pool(curr_node, 2, 2)
    size = int(size/2) #28

    # Convs 3-6
    convs, weights, biases, curr_node = conv_step(convs, weights, biases, curr_node, 1, 1, in_features, 128, dropout)
    convs, weights, biases, curr_node = conv_step(convs, weights, biases, curr_node, 3, 1, 128, 256, dropout)
    convs, weights, biases, curr_node = conv_step(convs, weights, biases, curr_node, 1, 1, 256, 256, dropout)
    convs, weights, biases, curr_node = conv_step(convs, weights, biases, curr_node, 1, 1, 256, 512, dropout)

    # Max Pool 3
    curr_node = pool(curr_node, 2, 2)
    size = int(size/2) #14

    # Convs 7-16
    for _ in range(4):
        convs, weights, biases, curr_node = conv_step(convs, weights, biases, curr_node, 1, 1, 512, 256, dropout)
        convs, weights, biases, curr_node = conv_step(convs, weights, biases, curr_node, 3, 1, 256, 512, dropout)
    convs, weights, biases, curr_node = conv_step(convs, weights, biases, curr_node, 1, 1, 512, 512, dropout)
    convs, weights, biases, curr_node = conv_step(convs, weights, biases, curr_node, 3, 1, 512, 1024, dropout)

    # Max Pool 4
    curr_node = pool(curr_node, 2, 2)
    size = int(size/2) #7

    # Convs 17-24
    for _ in range(2):
        convs, weights, biases, curr_node = conv_step(convs, weights, biases, curr_node, 1, 1, 1024, 512, dropout)
        convs, weights, biases, curr_node = conv_step(convs, weights, biases, curr_node, 3, 1, 512, 1024, dropout)
    for i in range(5):
        if i == 1:
            s = 2
        else:
            s = 1
        convs, weights, biases, curr_node = conv_step(convs, weights, biases, curr_node, 3, s, 1024, 1024, dropout)
    size = int(size/2) #3

    flat_dimension = size * size * 1024 # 7 by 7 by 1024
    flatten = tf.reshape(curr_node, [-1, flat_dimension])

    # FC 1
    out_features = 4096
    stddev = np.sqrt(2 / flat_dimension)
    W = weight([flat_dimension, out_features], stddev)
    b = bias([out_features])
    weights.append(W)
    biases.append(b)
    dense1 = dense(flatten, W, b, dropout, leaky=True)
    in_features = out_features

    # FC 2
    out_features = num_cells * num_cells * (num_boxes * 5)  # + num_classes)
    stddev = np.sqrt(2 / in_features)
    linear_W = tf.Variable(tf.truncated_normal([in_features, out_features], stddev), dtype=tf.float32)
    linear_b = tf.Variable([out_features], dtype=tf.float32)
    dense2 = tf.matmul(dense1, linear_W) + linear_b #tf.nn.xw_plus_b(dense1, linear_W, linear_b)
    weights.append(linear_W)
    biases.append(linear_b)
    logits = tf.reshape(dense2, [-1, num_cells, num_cells, num_boxes * 5])  # +num_classes])

    variables = []
    for w in weights:
        variables.append(w)
    for b in biases:
        variables.append(b)

    return logits, variables
