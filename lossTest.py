import tensorflow as tf
import numpy as np
from utils import convert_xyxy_to_xywh, IoU_parallel, repeat_tensor, separate_trues
from generator import Generator
from matplotlib import pyplot as plt
from yoloStructure import tiny_yolo

BATCH_SIZE = 1
NUM_BOXES =2
NUM_CELLS = 4

TRAIN_CSV_PATH = "D:/PCImages/train.csv"
generator = Generator(TRAIN_CSV_PATH, one_hot=False, shuffle_data=True, num_cells=NUM_CELLS)

#data, labels = generator(BATCH_SIZE)
#print(labels)

init = tf.global_variables_initializer()
with tf.Session() as sess:
    _ = sess.run(init) # initializes network?
    #prediction, _, = sess.run(tiny_yolo(data, num_boxes=2, num_cells=4))

def get_cost(mode, h, y, num_boxes=NUM_BOXES, lambda_coord=1.0, lambda_noobj=0.5):
    regression_loss = 0
    classification_loss = 0
    confidence_loss = 0
    avg_IoU = 0
    for i in range(BATCH_SIZE):
        y_reshaped = tf.reshape(y[i, :, :, :], [-1, 5])
        h_reshaped = tf.reshape(h[i, :, :, :], [-1, num_boxes, 5])
        if mode=='RESHAPE':
            return y_reshaped, h_reshaped
        h_w, h_wo, y_w, y_wo = separate_trues(h_reshaped, y_reshaped)
        if mode=='SEPARATE':
            return h_w, h_wo, y_w, y_wo
        iou = IoU_parallel(y_w, h_w)
        if mode=='IOU':
            return iou
        max_IoU_idx = tf.argmax(iou)
        if mode=='ARGMAX':
            return max_IoU_idx
        if num_boxes==1:
            h_max = h_w[max_IoU_idx[0],0,:4]
        else:
            h_max = h_w[max_IoU_idx[0], max_IoU_idx[1], :4]
        y_max = y_w[max_IoU_idx[0], :4]
        if mode=='MAX':
            return max_IoU_idx, h_max, y_max
        regression_loss += lambda_coord * tf.reduce_sum(
            tf.math.add(tf.squared_difference(h_max[0], y_max[0]), tf.squared_difference(h_max[1], y_max[1])))
        regression_loss += lambda_coord * tf.reduce_sum(
            tf.math.add(tf.squared_difference(tf.sqrt(h_max[2]), tf.sqrt(y_max[2])),
                        tf.squared_difference(tf.sqrt(h_max[3]), tf.sqrt(y_max[3]))))
        if mode=='REGRESSION':
            return regression_loss
        y_w_tiled = repeat_tensor(y_w[:, 4], tf.shape(h_w[:, :, 4])[1])
        if mode=='TILE':
            return y_w_tiled
        confidence_loss += tf.reduce_sum(tf.squared_difference(h_w[:, :, 4], y_w_tiled))
        confidence_loss -= lambda_noobj * tf.reduce_sum(h_wo[:, :, 4])
        if mode=='CONFIDENCE':
            return confidence_loss
        avg_IoU += tf.reduce_mean(iou)
        if mode=='AVG_IOU':
            return avg_IoU
    return abs(confidence_loss) + regression_loss

if __name__ == '__main__':
    while True:
        data, labels = generator(BATCH_SIZE)
        print(labels)
        plt.imshow(data[0,:,:,0])
        plt.show()
        randomArr = np.random.rand(NUM_CELLS, NUM_CELLS, NUM_BOXES * 5)
        r = randomArr.reshape(BATCH_SIZE, randomArr.shape[0], randomArr.shape[1], randomArr.shape[2])
        with tf.Session() as sess:
            #loss = sess.run(get_cost(None, labels, labels, num_boxes=1))
            #print(loss)
            loss = sess.run(get_cost(None, r, labels, num_boxes=NUM_BOXES))
            print(loss)