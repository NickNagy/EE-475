import tensorflow as tf
import numpy as np


# from matplotlib.patches import Rectangle
# from matplotlib import pyplot as plt

# TODO: only works for 2-class problem right now
def convert_xyxy_to_xywh(img_shape, coords, num_cells):
    # returns a 3d array of shape num_cells*num_cells*4, where each index (i,j,:) corresponds to a cell space in img
    # if coordinates of an object fall in a cell space, then cell_array(i,j,:) = (x, y, width, height, label) of the
    # object, where x and y are the centerpoints of the ground truth box. All four values are normalized wrt the cell
    # space
    cell_w = img_shape[0] / num_cells
    cell_h = img_shape[1] / num_cells
    cell_array = np.zeros((num_cells, num_cells, 5))
    for i in range(len(coords)):
        [x1, y1, x2, y2, label] = coords[i]
        x_center = (x1 + x2) / 2
        y_center = (y1 + y2) / 2
        cell_x = int(x_center / cell_w)
        cell_y = int(y_center / cell_h)
        if cell_x == 0:
            box_x = x_center
        else:
            box_x = (x_center - cell_w * cell_x) / (cell_w * cell_x)
        if cell_y == 0:
            box_y = y_center
        else:
            box_y = (y_center - cell_h * cell_y) / (cell_h * cell_y)
        box_w = (x2 - x1) / cell_w
        box_h = (y2 - y1) / cell_h
        cell_array[cell_y, cell_x, :] = (box_x, box_y, box_w, box_h, label)
    return cell_array

def get_max_conf_cell(input, num_boxes):
    boxes = tf.reshape(input[:,:,:], [-1, num_boxes, 5])
    max_conf_idx_arr = tf.argmax(boxes[:,:,4])
    max_conf_box = tf.argmax(max_conf_idx_arr)
    max_conf_cell = max_conf_idx_arr[max_conf_box]
    box = boxes[max_conf_cell, max_conf_box, :]
    return [[tf.cast(max_conf_cell, tf.float32), box[0], box[1], box[2], box[3]]]

def convert_xywh_to_xyxy(cell_array, num_cells=7, img_w=224, img_h=224):
    '''
    :param cell_array: of the form
        [[cell, x, y, w, h]] OR [[[x, y, w, h],...]]
    :param single: bool, True if input is a single [[cell, x, y, w, h]], false otherwise
    :return: coords in the form
        [[x1, y1, x2, y2]]
    '''
    cell_w = img_w / num_cells
    cell_h = img_h / num_cells
    cell_x = cell_array[:,0]%(num_cells)
    cell_y = (cell_array[:,0]/(num_cells)).astype(int)
    x_condlist = [cell_x[0]>0, cell_x[0]==0]
    x_choicelist = [np.multiply((cell_array[:,1]+1.0),cell_w*cell_x), cell_array[:,1]]
    y_condlist = [cell_y[0]>0, cell_y[0]==0]
    y_choicelist = [np.multiply((cell_array[:,2]+1.0),cell_h*cell_y), cell_array[:,2]]
    x = np.select(x_condlist, x_choicelist)
    y = np.select(y_condlist, y_choicelist)
    w = cell_w*cell_array[:,3]
    h = cell_h*cell_array[:,4]
    x1 = np.maximum(0, np.subtract(x, 0.5*w))
    y1 = np.maximum(0, np.subtract(y, 0.5*h))
    x2 = np.minimum(img_w, np.add(x, 0.5*w))
    y2 = np.minimum(img_h, np.add(y, 0.5*h))
    x1y1 = np.concatenate(([x1], [y1])).transpose()
    x2y2 = np.concatenate(([x2], [y2])).transpose()
    return np.concatenate((x1y1, x2y2), axis=1).astype(int)

# from: https://github.com/jakeret/tf_unet/tree/master/tf_unet
def get_image_summary(img):
    V = tf.slice(img, (0, 0, 0, 0), (1, -1, -1, 1))
    V -= tf.reduce_min(V)
    V /= tf.reduce_max(V)
    V *= 255
    img_w = tf.shape(img)[1]
    img_h = tf.shape(img)[2]
    V = tf.reshape(V, tf.stack((img_w, img_h, 1)))
    V = tf.transpose(V, (2, 0, 1))
    V = tf.reshape(V, tf.stack((-1, img_w, img_h, 1)))
    return V


# TODO: pass multiple truths and predictions at once
def IoU(true, pred):
    pred_x = pred[0]
    pred_y = pred[1]
    pred_w = pred[2]
    pred_h = pred[3]
    true_x = true[0]
    true_y = true[1]
    true_w = true[2]
    true_h = true[3]
    xA = tf.math.maximum((pred_x - 0.5 * pred_w), (true_x - 0.5 * true_w))
    yA = tf.math.maximum((pred_y - 0.5 * pred_h), (true_y - 0.5 * true_h))
    xB = tf.math.minimum((pred_x + 0.5 * pred_w), (true_x + 0.5 * true_w))
    yB = tf.math.minimum((pred_y + 0.5 * pred_h), (true_y + 0.5 * true_h))
    inter_area = tf.maximum((xB - xA), 0) * tf.maximum((yB - yA), 0)
    pred_area = pred_w * pred_h
    true_area = true_w * true_h
    return tf.reduce_mean(inter_area / (pred_area + true_area - inter_area))

def repeat_tensor(x, num_repeats):
    """
    :param x: a tensor of shape [n]
    :param num_repeats: how many times to copy tensor
    :return: a copied tensor of shape [n, num_repeats]
    """
    x = tf.reshape(x, [tf.shape(x)[0],1])#,-1])#[x.get_shape().as_list()[0],-1])
    return tf.tile(x, [1, num_repeats])

def separate_trues(x, y):
    # returns x and sorted y into present class or not
    s = y[:, 4]
    _, idx = tf.nn.top_k(s, tf.shape(y)[0])#y.get_shape()[0].value)
    x = tf.gather(x, idx)
    y = tf.gather(y, idx)
    cutoff = tf.argmin(y)[4]
    x_with_box = x[:cutoff, :, :]
    x_without_box = x[cutoff:, :, :]
    y_with_box = y[:cutoff, :]
    y_without_box = y[cutoff:, :]
    return x_with_box, x_without_box, y_with_box, y_without_box

def get_max_confidence_box(lgts):
    s = lgts[:,:,4]
    _, idx = tf.nn.top_k(s, tf.shape(lgts)[0])
    lgts = tf.gather(lgts, idx)
    return lgts[0,:,:4]

# parallel implementation of IoU
def IoU_parallel(true, pred):
    num_boxes = pred[:,:,0].get_shape().as_list()[1]
    pred_x = pred[:, :, 0]
    pred_y = pred[:, :, 1]
    pred_w = pred[:, :, 2]
    pred_h = pred[:, :, 3]
    true_x = repeat_tensor(true[:,0], num_boxes)
    true_y = repeat_tensor(true[:,1], num_boxes)
    true_w = repeat_tensor(true[:,2], num_boxes)
    true_h = repeat_tensor(true[:,3], num_boxes)
    xA = tf.math.maximum(tf.subtract(pred_x, 0.5*pred_w), (tf.subtract(true_x, 0.5*true_w)))
    yA = tf.math.maximum(tf.subtract(pred_y, 0.5*pred_h), (tf.subtract(true_y, 0.5*true_h)))
    xB = tf.math.minimum(tf.add(pred_x, 0.5*pred_w), (tf.add(true_x, 0.5*true_w)))
    yB = tf.math.minimum(tf.add(pred_y, 0.5*pred_h), (tf.add(true_y, 0.5*true_h)))
    inter_area = tf.multiply(tf.math.maximum(tf.subtract(xB, xA), tf.zeros(shape=tf.shape(xB),dtype=tf.float32)),
                             tf.math.maximum(tf.subtract(yB, yA), tf.zeros(shape=tf.shape(yB),dtype=tf.float32)))
    pred_area = tf.multiply(pred_w, pred_h)
    true_area = tf.multiply(true_w, true_h)
    return tf.divide(inter_area, tf.subtract(tf.add(pred_area, true_area), inter_area))

def remove_borders(frame):
    top = 0
    while np.sum(frame[top,:]) == 0:
        top += 1
    bottom = frame.shape[0]-1
    while np.sum(frame[bottom,:])==0:
        bottom -= 1
    return frame[top:bottom, :]
