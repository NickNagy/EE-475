import tensorflow as tf
import numpy as np
from utils import convert_xyxy_to_xywh, IoU_parallel, repeat_tensor, separate_trues
from generator import Generator
from matplotlib import pyplot as plt
from yoloClasses import YoloNetwork
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

def zero_cond():
    zero = tf.constant(0, tf.float32)
    return zero, zero, zero, zero, zero

def present_object_cost(h, y, num_boxes, lambda_coord=1.0):
    iou = IoU_parallel(y, h)
    max_IoU_idx = tf.argmax(iou)
    if num_boxes == 1:
        h_max = h[max_IoU_idx[0],0,:4]
    else:
        h_max = h[max_IoU_idx[0],max_IoU_idx[1],:4]
    y_max = y[max_IoU_idx[0], :4]
    regression_loss_1 = lambda_coord * tf.reduce_sum(tf.math.add(tf.squared_difference(h_max[0], y_max[0]),
                                                               tf.squared_difference(h_max[1], y_max[1])))
    regression_loss_2 = lambda_coord * tf.reduce_sum(tf.math.add(tf.squared_difference(tf.sqrt(h_max[2]),
                                                                                      tf.sqrt(y_max[2])),
                                                                tf.squared_difference(tf.sqrt(h_max[3]),
                                                                                      tf.sqrt(y_max[3]))))
    y_tiled = repeat_tensor(y[:,4], tf.shape(h[:,:,4])[1])
    confidence_loss = tf.reduce_sum(tf.squared_difference(h[:,:,4], y_tiled))
    return confidence_loss, regression_loss_1, regression_loss_2, tf.reduce_mean(iou), h_max[2:]

def get_cost(mode, h, y, num_boxes=NUM_BOXES, lambda_coord=1.0, lambda_noobj=0.5):
    regression_loss = 0
    confidence_loss = 0
    avg_IoU = 0
    for i in range(BATCH_SIZE):
        y_reshaped = tf.reshape(y[i, :, :, :], [-1, 5])
        h_reshaped = tf.reshape(h[i, :, :, :], [-1, num_boxes, 5])
        if mode=='RESHAPE':
            return y_reshaped, h_reshaped
        h_w, h_wo, y_w, y_wo = separate_trues(h_reshaped, y_reshaped)
        confidence_loss -= lambda_noobj * tf.reduce_sum(h_wo[:, :, 4])
        if mode=='CONFIDENCE_NOOBJ':
            return confidence_loss
        cl, rl_1, rl_2, avg_iou, h_max_width_height = tf.cond(tf.shape(h_w)[0]>0,
                                                        lambda: present_object_cost(h_w, y_w, num_boxes, lambda_coord),
                                                        lambda: zero_cond())
        if mode=='PRESENT_OBJ':
            return cl, rl_1, rl_2, avg_iou, h_max_width_height
        confidence_loss += cl
        regression_loss += rl_1 + rl_2
        avg_IoU += avg_iou
        '''if mode=='SEPARATE':
            return h_w, tf.shape(h_w)#h_wo, y_w, y_wo
        iou = IoU_parallel(y_w, h_w)
        if mode=='IOU':
            return iou, tf.shape(iou)
        if tf.shape(iou)[1] is not None:
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
            return avg_IoU'''
    return abs(confidence_loss) + regression_loss

#model = YoloNetwork(batch_size=BATCH_SIZE, num_cells=NUM_CELLS, num_boxes=NUM_BOXES)

def test_logits():
    with tf.Session() as sess:
        # Initialize
        data, _ = generator(BATCH_SIZE)
        model = YoloNetwork(batch_size=BATCH_SIZE, num_cells=NUM_CELLS, num_boxes=NUM_BOXES)
        print(model.variables)
        init_op = tf.variables_initializer(model.variables)
        #_, variables = tiny_yolo(data, num_boxes=NUM_BOXES, num_cells=NUM_CELLS)  # = model.get_logits()
        #print(variables)
        sess.run(init_op)
        while True:
            data, labels = generator(BATCH_SIZE)
            print("TRUE: ")
            print(labels)
            plt.imshow(data[0, :, :, 0])
            plt.show()
            logits = sess.run(model.get_logits(), feed_dict={model.x:data, model.y:labels})
            print("PREDICTION: ")
            print(logits)
            cl, rl_1, rl_2, avg_iou, h_max_width_height = sess.run(get_cost('PRESENT_OBJ', logits,
                                                                            tf.cast(labels, tf.float32),
                                                                            num_boxes=NUM_BOXES))
            print("CL: " + str(cl))
            print("RL (x,y): " + str(rl_1))
            print("RL (w,h): " + str(rl_2))
            try:
                print("Pred Width: " + str(h_max_width_height[0]))
                print("Pred Height: " + str(h_max_width_height[1]))
            except:
                continue
            loss = sess.run(get_cost(None, logits, tf.cast(labels, tf.float32), num_boxes=NUM_BOXES))
            print("LOSS: " + str(loss))

if __name__ == '__main__':
    test_logits()
    '''while True:
        data, labels = generator(BATCH_SIZE)
        print(labels)
        plt.imshow(data[0,:,:,0])
        plt.show()
        randomArr = np.random.rand(NUM_CELLS, NUM_CELLS, NUM_BOXES * 5)
        r = randomArr.reshape(BATCH_SIZE, randomArr.shape[0], randomArr.shape[1], randomArr.shape[2])
        with tf.Session() as sess:
            #h_w, h_w_shape = sess.run(get_cost("IOU", r, labels, num_boxes=1))
            #print(h_w)
            #print(h_w_shape)
            loss = sess.run(get_cost(None, r, labels, num_boxes=NUM_BOXES))
            print(loss)'''
