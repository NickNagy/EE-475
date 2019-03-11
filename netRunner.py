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
from utils import convert_xywh_to_xyxy, get_max_conf_cell, remove_borders
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
import cv2
from scipy.misc import imresize

# these paths should point to csv files where each line is in the format:
#       path_to_image, x1, y1, x2, y2, class
# the generator class can train one-hot (no boxes) problems by ignoring the x and y coordinates on the line
# class is an int (or more accurately a string of an integer). Make sure you know which int represents which class.
TRAIN_CSV_PATH = "D:/PCImages/train_exist.csv"
VALIDATION_CSV_PATH = "D:/PCImages/validation.csv"

# path(s) to where model will be saved after training
OUTPUT_PATH = "C://Users//Nick Nagy//Desktop//Python//Capstone"

# if you want to further train a previously saved model, set restore to TRUE, and assign the restore path to the
# location of the saved model
restore = True
RESTORE_PATH = OUTPUT_PATH
NUM_CELLS = 7
NUM_BOXES = 2

train_batch_size = 1
validation_batch_size = train_batch_size#1

learning_rate = 0.1
dropout = 0.75

train_generator = Generator(TRAIN_CSV_PATH, one_hot=False, shuffle_data=True, xywh=True)
validation_generator = Generator(VALIDATION_CSV_PATH, one_hot=False, shuffle_data=True, xywh=True)

epochs = 10

training_iters = int(train_generator.length() / train_batch_size) + int(train_generator.length()%train_batch_size > 0)

yolo = YoloNetwork(batch_size=train_batch_size)

def train(epochs=epochs):
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
        init_op = tf.variables_initializer(model.variables)
        sess.run(init_op)
        model.restore(sess, OUTPUT_PATH)
        for i in range(50):
            test_image, test_coords = generator(1)
            # with tf.Session() as sess:
            prediction = sess.run(model.predicter, feed_dict={model.x: test_image, model.y: test_coords})#yolo.predict(RESTORE_PATH, test_image)
            #prediction = model.predict(OUTPUT_PATH, test_image)
            #print(prediction)
            pred_coords = convert_xywh_to_xyxy(np.asarray(prediction[:5]), num_cells=NUM_CELLS)[0]
            true_cell = sess.run(get_max_conf_cell(test_coords, 1))
            true_coords = convert_xywh_to_xyxy(np.asarray(true_cell), num_cells=NUM_CELLS)
            fig, ax = plt.subplots(1)
            ax.imshow(test_image[0, :, :, 0])
            [true_x1, true_y1, true_x2, true_y2] = true_coords[0, :]
            [pred_x1, pred_y1, pred_x2, pred_y2] = pred_coords[:4]
            print([true_x1, true_y1, true_x2, true_y2])
            print([pred_x1, pred_y1, pred_x2, pred_y2])
            print("Confidence: " + str(prediction[0][4]))
            true_rect = Rectangle((true_x1, true_y1), true_x2 - true_x1, true_y2 - true_y1, edgecolor='g', fill=False)
            ax.add_patch(true_rect)
            if prediction[0][4] > threshold:
                pred_rect = Rectangle((pred_x1, pred_y1), pred_x2 - pred_x1, pred_y2 - pred_y1, edgecolor='r', fill=False)
                ax.add_patch(pred_rect)
            plt.savefig(OUTPUT_PATH + '//' + str(i) + '.jpg')
            plt.close()
            print('********************')

def camera_predict(model, threshold = 0.5):
    cap = cv2.VideoCapture(0)
    with tf.Session() as sess:
        init_op = tf.variables_initializer(model.variables)
        sess.run(init_op)
        model.restore(sess, OUTPUT_PATH)
        y_dummy = np.empty((1, NUM_CELLS, NUM_CELLS, 5))
        while True:
            ret, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            img = imresize(remove_borders(gray), (224, 224))
            prediction = sess.run(model.predicter, feed_dict={model.x: img.reshape(1, 224, 224, 1), model.y: y_dummy})
            pred_coords = convert_xywh_to_xyxy(np.asarray(prediction[:5]), num_cells=NUM_CELLS)[0]
            #print(prediction[0])
            if prediction[0][4] > threshold:
                print(pred_coords)
                cv2.rectangle(img, (pred_coords[0], pred_coords[1]), (pred_coords[2], pred_coords[3]), (255,0,0), 2, cv2.LINE_AA)
            cv2.imshow('', img)
            if cv2.waitKey(1) == 27:
                break

if __name__ == '__main__':
    #train(10)
    predict(yolo, train_generator)
    #camera_predict(yolo)
