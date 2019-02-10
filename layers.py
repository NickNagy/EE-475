import tensorflow as tf

def weight(shape, stddev, trainable=True):
    return tf.Variable(tf.truncated_normal(shape, stddev), trainable=trainable)

def bias(shape, trainable=True):
    return tf.Variable(tf.constant(0.1, shape=shape), trainable=trainable)

def conv2d(x, W, b=0):
    # TODO: add dropout and bias
    with tf.name_scope("conv2d"):
        return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='VALID') + b

# TODO: if different shapes, layer2 should be resized to layer 1
def residual(layer1, layer2):
    return tf.math.add(layer1, layer2)

# TODO:
#def dense(x, units):
#    return tf.layers.dense(inputs=x, units=units, activation=tf.nn.relu)

def dense(x, W, b):
    return tf.nn.relu(tf.nn.xw_plus_b(x, W, b))
