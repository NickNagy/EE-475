import numpy as np
from scipy.misc import imresize
from utils import convert_xywh_to_xyxy, remove_borders
import cv2

VARS_PATH = "C://Users//Nick Nagy//Desktop//Python//Capstone//Variables//"

# TODO: better implementation
pool_layers = {'1':2, '2': 2, '3':2, '4':2, '5':2}

def load_weight(path, layer):
    return np.load(path + 'weights_' + str(layer) + '.npy')

def load_bias(path, layer):
    return np.load(path + 'biases_' + str(layer) + '.npy')

def load_vars(path):
    print("Loading Variables...")
    idx = 0
    weights_list = []
    biases_list = []
    while True:
        try:
            weights_list.append(load_weight(path, idx))
            biases_list.append(load_bias(path, idx))
            idx += 1
        except:
            break
    return weights_list, biases_list

# TODO: parallel implementation?
def max_pool(input, s):
    dim = int(input.shape[1]/s)
    k = input.shape[3]

    output = np.zeros(shape=(1, dim, dim, k))
    for i in range(dim):
        for j in range(dim):
            output[0, i,j, :] = np.ndarray.max(input[0, s*i:s*(i+1), s*j:s*(j+1), :])
    return output

def pad(input, k):
    pad_width = int(0.5*(input.shape[0] + k))
    return np.pad(input, pad_width, 'reflect')

def relu(input):
    return np.maximum(input, 0)#np.zeros(shape=input.shape))

# from https://github.com/renmengye/np-conv2d/blob/master/conv2d.py
def array_offset(x):
    """Get offset of array data from base data in bytes."""
    if x.base is None:
        return 0

    base_start = x.base.__array_interface__['data'][0]
    start = x.__array_interface__['data'][0]
    return start - base_start

# from https://github.com/renmengye/np-conv2d/blob/master/conv2d.py
def calc_pad(pad, in_siz, out_siz, stride, ksize):
    if pad == 'SAME':
        return (out_siz - 1) * stride + ksize - in_siz
    elif pad == 'VALID':
        return 0
    else:
        return pad

# from https://github.com/renmengye/np-conv2d/blob/master/conv2d.py
def calc_size(h, kh, pad, sh):
    if pad == 'VALID':
        return np.ceil((h - kh + 1) / sh)
    elif pad == 'SAME':
        return np.ceil(h / sh)
    else:
        return int(np.ceil((h - kh + pad + 1) / sh))

# from https://github.com/renmengye/np-conv2d/blob/master/conv2d.py
def extract_sliding_windows(x, ksize, pad, stride, floor_first=True):

    n = x.shape[0]
    h = x.shape[1]
    w = x.shape[2]
    c = x.shape[3]
    kh = ksize[0]
    kw = ksize[1]
    sh = stride[0]
    sw = stride[1]

    h2 = int(calc_size(h, kh, pad, sh))
    w2 = int(calc_size(w, kw, pad, sw))
    ph = int(calc_pad(pad, h, h2, sh, kh))
    pw = int(calc_pad(pad, w, w2, sw, kw))

    ph0 = int(np.floor(ph / 2))
    ph1 = int(np.ceil(ph / 2))
    pw0 = int(np.floor(pw / 2))
    pw1 = int(np.ceil(pw / 2))

    if floor_first:
        pph = (ph0, ph1)
        ppw = (pw0, pw1)
    else:
        pph = (ph1, ph0)
        ppw = (pw1, pw0)
    x = np.pad(
        x, ((0, 0), pph, ppw, (0, 0)),
        mode='constant',
        constant_values=(0.0, ))

    x_sn, x_sh, x_sw, x_sc = x.strides
    y_strides = (x_sn, sh * x_sh, sw * x_sw, x_sh, x_sw, x_sc)
    y = np.ndarray((n, h2, w2, kh, kw, c),
                   dtype=x.dtype,
                   buffer=x.data,
                   offset=array_offset(x),
                   strides=y_strides)
    return y

# from https://github.com/renmengye/np-conv2d/blob/master/conv2d.py
def conv2d(x, w, pad='SAME', stride=(1, 1)):
    ksize = w.shape[:2]
    x = extract_sliding_windows(x, ksize, pad, stride)
    ws = w.shape
    w = w.reshape([ws[0] * ws[1] * ws[2], ws[3]])
    xs = x.shape
    x = x.reshape([xs[0] * xs[1] * xs[2], -1])
    y = x.dot(w)
    y = y.reshape([xs[0], xs[1], xs[2], -1])
    return y

def convolution(input, weight, bias):
    xW = conv2d(input, weight)
    return relu(np.add(xW, bias))

def model(input, weights, biases, pool_layers):
    curr_node = input
    layer = 0
    while True:
        try:
            curr_node = convolution(curr_node, weights[layer], biases[layer])
            if str(layer) in pool_layers.keys():
                curr_node = max_pool(curr_node, pool_layers[str(layer)])
            layer += 1
        except:
            break
    return curr_node

def get_max_conf_cell(logits, num_boxes):
    boxes = logits[:,:,:].reshape(-1, num_boxes, 5)
    max_conf_idx_arr = np.argmax(boxes[:,:,4], axis=0)
    max_conf_box = np.argmax(max_conf_idx_arr)
    max_conf_cell = max_conf_idx_arr[max_conf_box]
    box = boxes[max_conf_cell, max_conf_box, :]
    return [max_conf_cell, box[0], box[1], box[2], box[3]]

def predict(input, weights, biases, pool_layers, num_boxes=3, num_cells=7):
    logits = model(input.reshape(1, input.shape[0], input.shape[1],1), weights, biases, pool_layers)
    pred = get_max_conf_cell(logits, num_boxes)
    return convert_xywh_to_xyxy(np.asarray([pred]), num_cells)[0]

if __name__ == '__main__':
    w,b = load_vars(VARS_PATH)
    cap = cv2.VideoCapture(0)
    while True:
        _, frame = cap.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        prediction = predict(imresize(remove_borders(frame),(224,224)),w,b,pool_layers)
