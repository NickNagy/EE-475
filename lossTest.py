import tensorflow as tf
import numpy as np
from utils import convert_xyxy_to_xywh, convert_xywh_to_xyxy, IoU_parallel, repeat_tensor, separate_trues, get_max_conf_cell
from generator import Generator
from matplotlib import pyplot as plt
from yoloClasses import YoloNetwork
from yoloStructure import tiny_yolo

BATCH_SIZE = 5
NUM_BOXES = 2
NUM_CELLS = 7

TRAIN_CSV_PATH = "D:/PCImages/train.csv"
generator = Generator(TRAIN_CSV_PATH, one_hot=False, shuffle_data=True, num_cells=NUM_CELLS)

#data, labels = generator(BATCH_SIZE)
#print(labels)

init = tf.global_variables_initializer()
with tf.Session() as sess:
    _ = sess.run(init) # initializes network?
    #prediction, _, = sess.run(tiny_yolo(data, num_boxes=2, num_cells=4))


def test_conversion(coords):
    xywh = convert_xyxy_to_xywh((224, 224), coords, NUM_CELLS)
    with tf.Session() as sess:
        cell = sess.run(get_max_conf_cell(xywh, 1))
    xyxy = convert_xywh_to_xyxy(np.asarray(cell), num_cells=NUM_CELLS)
    return xywh, cell, xyxy

def test_all_coord_conversions():
    with open(TRAIN_CSV_PATH, 'r') as file:
        while True:
            _, x1, y1, x2, y2, label = file.readline().split(',')
            coords = [int(x1), int(y1), int(x2), int(y2), int(label)]
            print(coords)
            _, _, xyxy = test_conversion([coords])
            print(xyxy)
            print('****************************')

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
    return abs(confidence_loss) + regression_loss

#model = YoloNetwork(batch_size=BATCH_SIZE, num_cells=NUM_CELLS, num_boxes=NUM_BOXES)

def get_prediction(mode, logits, num_boxes):
    h = tf.reshape(logits[0, :,:,:], [-1, num_boxes, 5])
    max_conf_idx_arr = tf.argmax(h[:, :, 4])
    max_conf_box = tf.argmax(max_conf_idx_arr)
    max_conf_cell = max_conf_idx_arr[max_conf_box]
    if mode=='CELL':
        return max_conf_cell
    p_box = h[max_conf_cell, max_conf_box, :]
    if mode=='BOX':
        return p_box
    prediction = [[tf.cast(max_conf_cell, tf.float32), p_box[0], p_box[1], p_box[2], p_box[3], p_box[4]]]
    for i in range(1, BATCH_SIZE):
        h = tf.reshape(logits[i,:,:,:], [-1, num_boxes, 5])
        max_conf_idx_arr = tf.argmax(h[:,:,4])
        max_conf_box = tf.argmax(max_conf_idx_arr)
        max_conf_cell = max_conf_idx_arr[max_conf_box]
        p_box = h[max_conf_cell, max_conf_box, :]
        prediction = tf.concat([prediction, [[tf.cast(max_conf_cell, tf.float32), p_box[0], p_box[1], p_box[2], p_box[3], p_box[4]]]], 0)
    return prediction

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
            pred = sess.run(get_prediction(None, logits, NUM_BOXES))
            print(pred)
            print("CONVERTED PREDICTION: ")
            converted = convert_xywh_to_xyxy(pred[:5], num_cells=NUM_CELLS)
            print(converted)
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
    #test_all_coord_conversions()
    #test_logits()
    xywh, cell, xyxy = test_conversion([[68, 192, 88, 215, 1]])
    print(xywh)
    print(cell)
    print(xyxy)
