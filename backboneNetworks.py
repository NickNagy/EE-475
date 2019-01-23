import tensorflow as tf
import numpy as np

def weight(shape, stddev):
    return tf.Variable(tf.truncated_normal(shape, stddev))

def conv2d(x, W, b=0):
    # TODO: add dropout and bias
    return tf.nn.conv2d(x, W, strides=[1,1,1,1], padding='VALID') + b

def residual(layer1, layer2):
    return tf.math.add(layer1, layer2)

def vgg_19(x, num_classes=1, kernel_size=3):
    w,h = x.shape # should be 224x224
    
    size = w
    stddev = np.sqrt(2/(kernel_size * kernel_size))
    
    weights = []
    convs = []

    out_features = 64
    curr_input = x
    
    # conv layers
    while size > 7:
        stddev = np.sqrt(2/(kernel_size*kernel_size*out_features))
        if size == 224 or size == 112:
            size_layers = 2
        else:
            size_layers = 4
        for layer in range(size_layers):
            if layer == 0:
                if size == 224:
                    in_features = 1
                else:
                    in_features = out_features/2
            else:
                in_features = out_features
                W = weight(shape=[in_features,kernel_size,kernel_size], stddev)
                weights.append(W)
                conv = tf.nn.relu(conv2d(curr_input, W))
                convs.append(conv)
                curr_input = conv
        #  pool
        pool_layer = tf.nn.max_pool(curr_input, [1,2,2,1], [1,2,2,1], padding='VALID')
        curr_input = pool_layer
        out_features *= 2
        size /= 2
    
    # fc layers
    output = None
    
    return output, weights, convs

def resnet(x, num_classes=1, kernel_size=3, num_layers=34):
    
    w,h = x.shape
    
    size = w
    
    convs = []
    weights = []
    
    