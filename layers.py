import tensorflow as tf

def weight(shape, stddev):
    return tf.Variable(tf.truncated_normal(shape, stddev))


def conv2d(x, W, b=0):
    # TODO: add dropout and bias
    return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='VALID') + b


# TODO: if different shapes, layer2 should be resized to layer 1
def residual(layer1, layer2):
    return tf.math.add(layer1, layer2)