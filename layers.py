import tensorflow as tf
import numpy as np

def weight(shape, stddev, trainable=True):
    return tf.Variable(tf.truncated_normal(shape, stddev=stddev), trainable=trainable)

def bias(shape, trainable=True):
    return tf.Variable(tf.constant(0.1, shape=shape), trainable=trainable)

def conv2d(x, W, b, dropout, stride=1):
    with tf.name_scope("conv2d"):
        return tf.nn.dropout(tf.nn.bias_add(tf.nn.conv2d(x, W, strides=[1, stride, stride, 1], padding='SAME'), b), dropout)

# TODO: if different shapes, layer2 should be resized to layer 1
def residual(layer1, layer2):
    return tf.math.add(layer1, layer2)

def pool(x, kernel_size, stride):
    return tf.nn.max_pool(x, [1, kernel_size, kernel_size, 1], strides=[1, stride, stride, 1], padding='SAME')

def dense(x, W, b, dropout):
    return tf.nn.relu(tf.nn.dropout(tf.nn.xw_plus_b(x, W, b),dropout))
