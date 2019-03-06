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
        cell_array[cell_x, cell_y, :] = (box_x, box_y, box_w, box_h, label)
        # coords[i] = (box_x, box_y, box_w, box_h)
    return cell_array


def convert_xywh_to_xyxy_single(i, j, cell_w, cell_h, box):
    x_center = i * cell_w * (1 + box[0])
    y_center = j * cell_h * (1 + box[1])
    x1 = x_center - (box[2] / 2)
    x2 = x_center + (box[2] / 2)
    y1 = y_center - (box[3] / 2)
    y2 = y_center + (box[3] / 2)
    return x1, y1, x2, y2


'''
def convert_xywh_to_img_pred(img, pred_boxes, num_cells, save_path, name, threshold=0.7, best_box=False, true_boxes=None):
    w,h = img.shape
    cell_w = w / num_cells
    cell_h = h / num_cells
    fig, ax = plt.subplots(1)
    ax.imshow(img)
    for i in range(num_cells):
        for j in range(num_cells):
            if true_boxes is not None:
                truth_box = true_boxes[i,j,:]
                if np.sum(truth_box) > 0:
                    x1,y1,x2,y2 = convert_xywh_to_xyxy_single(i, j, cell_w, cell_h, truth_box)
                    rect = Rectangle((x1,y1), x2-x1, y2-y1, edgecolor='g', fill=False)
                    ax.add_patch(rect)
            for k in range(int(len(pred_boxes[i,j,:])/5)):
                pred_confidence = pred_boxes[i,j,k*5+4]
                if pred_confidence > threshold:
                    pred_box = pred_boxes[i, j, k * 5:k * 5 + 4]
                    x1,y1,x2,y2 = convert_xywh_to_xyxy_single(i,j,cell_w, cell_h, pred_box)
                    rect = Rectangle((x1,y1), x2-x1, y2-y1, edgecolor='r', fill=False)
                    ax.add_patch(rect)
    plt.savefig(save_path + name + ".jpg")
'''


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

# parallel implementation of IoU
def IoU_parallel(true, pred):
    true = tf.cast(true, tf.float32)
    num_boxes = pred[:,0].get_shape().as_list()
    half_const = tf.constant(0.5, shape=num_boxes)
    pred_x = pred[:,0]
    pred_y = pred[:,1]
    pred_w = pred[:,2]
    pred_h = pred[:,3]
    true_x = true[0]#tf.tile(true[:,0],[num_boxes])
    true_y = true[1]#tf.tile(true[:,1],[num_boxes])
    true_w = true[2]#tf.tile(true[:,2],[num_boxes])
    true_h = true[3]#tf.tile(true[:,3],[num_boxes])
    half_pred_w = tf.multiply(half_const, pred_w)
    half_pred_h = tf.multiply(half_const, pred_h)
    half_true_w = tf.multiply(half_const, true_w)
    half_true_h = tf.multiply(half_const, true_h)
    xA = tf.math.maximum(tf.subtract(pred_x, half_pred_w), (tf.subtract(true_x, half_true_w)))
    yA = tf.math.maximum(tf.subtract(pred_y, half_pred_h), (tf.subtract(true_y, half_true_h)))
    xB = tf.math.minimum(tf.add(pred_x, half_pred_w), (tf.add(true_x, half_true_w)))
    yB = tf.math.minimum(tf.add(pred_y, half_pred_h), (tf.add(true_y, half_true_h)))
    inter_area = tf.multiply(tf.math.maximum(tf.subtract(xB, xA), tf.zeros(shape=(num_boxes))), tf.math.maximum(tf.subtract(yB,yA),tf.zeros(shape=(num_boxes))))
    pred_area = tf.multiply(pred_w, pred_h)
    true_area = tf.multiply(true_w, true_h)
    return tf.divide(inter_area, tf.subtract(tf.add(pred_area, true_area), inter_area))

def test_IoU():
    true = tf.constant([.5, .5, .5, .5])
    pred = tf.constant([[.5, .5, .5, .5], [.5, .5, 1, 1], [0, 0, 1, 1], [0, .5, .5, .5]])
    results = IoU_parallel(true, pred)
    max_IoU_box = pred[tf.argmax(results),:]
    return results, max_IoU_box


'''
def IoU(true, pred):
    pred_x1 = pred[0]
    pred_y1 = pred[1]
    pred_x2 = pred[2]
    pred_y2 = pred[3]
    true_x1 = true[0]
    true_y1 = true[1]
    true_x2 = true[2]
    true_y2 = true[3]
    xA = tf.math.maximum(pred_x1, tf.transpose(true_x1))
    yA = tf.math.maximum(pred_y1, tf.transpose(true_y1))
    xB = tf.math.minimum(pred_x2, tf.transpose(true_x2))
    yB = tf.math.minimum(pred_y2, tf.transpose(true_y2))
    inter_area = tf.maximum((xB-xA+1),0)*tf.maximum((yB-yA+1),0)
    pred_area = (pred_x2-pred_x1+1)*(pred_y2-pred_y1+1)
    true_area = (true_x2-true_x1+1)*(true_y2-true_y1+1)
    return tf.reduce_mean(inter_area / (pred_area + tf.transpose(true_area) - inter_area))
'''

if __name__ == '__main__':
    with tf.Session() as sess:
        results, max_IoU_box = sess.run(test_IoU())
        print(results)
        print(max_IoU_box)
