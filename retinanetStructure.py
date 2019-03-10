"""
Python script for training convolutional neural networks.
- Nick

Note: Most of this has been tested on problems with two classes.
"""

import tensorflow as tf
import numpy as np
from generator import Generator
from oneHotClasses import OneHotNetwork, OneHotNetworkTrainer
from yoloClasses import YoloNetwork, YoloTrainer
import time
from utils import convert_xywh_to_xyxy, get_max_conf_cell
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle

# these paths should point to csv files where each line is in the format:
#       path_to_image, x1, y1, x2, y2, class
# the generator class can train one-hot (no boxes) problems by ignoring the x and y coordinates on the line
# class is an int (or more accurately a string of an integer). Make sure you know which int represents which class.
TRAIN_CSV_PATH = "D:/PCImages/train.csv"
VALIDATION_CSV_PATH = "D:/PCImages/validation.csv"

# path(s) to where model will be saved after training
OUTPUT_PATH = "C://Users//Nick Nagy//Desktop//Python//Capstone"

# if you want to further train a previously saved model, set restore to TRUE, and assign the restore path to the
# location of the saved model
restore = True
RESTORE_PATH = OUTPUT_PATH
NUM_CELLS = 7
NUM_BOXES = 2

train_batch_size = 5
validation_batch_size = train_batch_size#1

learning_rate = 0.001
dropout = 0.75

print("Initializing generators... " + str(time.time()))
train_generator = Generator(TRAIN_CSV_PATH, one_hot=False, shuffle_data=True, xywh=True)
validation_generator = Generator(VALIDATION_CSV_PATH, one_hot=False, shuffle_data=True, xywh=True)

epochs = 10
#print("Validation CSV Length: " + str(validation_generator.length()))
training_iters = int(train_generator.length() / train_batch_size) + int(train_generator.length()%train_batch_size > 0)
#print("Training Iterations: " + str(training_iters))

print("Initializing network... " + str(time.time()))
yolo = YoloNetwork(batch_size=train_batch_size)

def train():
    yolo_trainer = YoloTrainer(model=yolo, batch_size=train_batch_size, validation_batch_size=validation_batch_size,
                           opt_kwargs=dict(learning_rate=learning_rate))

    print("Beginning training... " + str(time.time()))
    yolo_trainer.train(train_generator, validation_generator, validation_generator.length(), training_iters,
                   RESTORE_PATH, OUTPUT_PATH, epochs=epochs, dropout=dropout, restore=restore)

def predict(model, generator):
    # TODO:
    threshold = 0.5
    plt.gray()
    with tf.Session() as sess:
        for t in range(10):
            test_image, test_coords = generator(train_batch_size)
            # with tf.Session() as sess:
            #    init_op = tf.variables_initializer(yolo.variables)
            #    sess.run(init_op)
            #    yolo.restore(sess, OUTPUT_PATH)
            #    prediction = sess.run(yolo.predicter, feed_dict={yolo.x: test_image, yolo.y: test_coords})#yolo.predict(RESTORE_PATH, test_image)
            prediction = model.predict(OUTPUT_PATH, test_image)
            #print(prediction)
            pred_coords = convert_xywh_to_xyxy(np.asarray(prediction[:5]), num_cells=NUM_CELLS)
            for i in range(test_image.shape[0]):
                true_cell = sess.run(get_max_conf_cell(test_coords[i, :, :, :], 1))
                true_coords = convert_xywh_to_xyxy(np.asarray(true_cell), num_cells=NUM_CELLS)
                fig, ax = plt.subplots(1)
                ax.imshow(test_image[i, :, :, 0])
                [true_x1, true_y1, true_x2, true_y2] = true_coords[0, :]
                [pred_x1, pred_y1, pred_x2, pred_y2] = pred_coords[i, :4]
                print([true_x1, true_y1, true_x2, true_y2])
                print([pred_x1, pred_y1, pred_x2, pred_y2])
                print("Confidence: " + str(prediction[i, 4]))
                true_rect = Rectangle((true_x1, true_y1), true_x2 - true_x1, true_y2 - true_y1, edgecolor='g', fill=False)
                ax.add_patch(true_rect)
                if prediction[i, 4] > threshold:
                    pred_rect = Rectangle((pred_x1, pred_y1), pred_x2 - pred_x1, pred_y2 - pred_y1, edgecolor='r', fill=False)
                    ax.add_patch(pred_rect)
                plt.savefig(OUTPUT_PATH + '//' + str(t) + '_' + str(i) + '.jpg')
                plt.close()
                print('********************')

if __name__ == '__main__':
    train()
    predict(yolo, train_generator)
