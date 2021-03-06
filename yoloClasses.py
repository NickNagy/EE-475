from __future__ import print_function, division, absolute_import, unicode_literals

import tensorflow as tf
import numpy as np
from yoloStructure import yolo, tiny_yolo
from utils import IoU, IoU_parallel, repeat_tensor, separate_trues, get_max_conf_cell
import os
import logging
import time

from tensorflow.python import debug as tf_debug

config = tf.ConfigProto()
config.gpu_options.allow_growth = True

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


# TODO: for now only designed to work with 1 class
# usually, the fifth index of each cell in logits represents a confidence score that ANY object is present in that cell.
# instead, I am using it as a class prediction.
class YoloNetwork(object):
    def __init__(self, batch_size=1, num_classes=2, num_cells=7, num_boxes=2):
        self.x = tf.placeholder("int32", shape=[None, None, None, 1], name="x")
        self.y = tf.placeholder("float32", shape=[None, num_cells, num_cells, 5], name="y")
        self.dropout = tf.placeholder(tf.float32, name="dropout_probability")

        self.batch_size = batch_size

        print("Building structure... " + str(time.time()))
        self.logits, self.variables = tiny_yolo(self.x, num_classes=num_classes, num_cells=num_cells,
                                                num_boxes=num_boxes)

        print("Defining cost function... " + str(time.time()))
        # cost, avg_IoU = self._get_cost(self.logits, num_boxes, num_cells)
        self.cost = self._get_cost(self.logits, num_boxes, num_cells)
        self.gradients_node = tf.gradients(self.cost, self.variables)

        self.num_cells = num_cells

        with tf.name_scope("results"):
            self.predicter = self._get_prediction(num_boxes)  # self.logits

    def _get_prediction(self, num_boxes):
        prediction = get_max_conf_cell(self.logits[0, :, :, :], num_boxes)
        for i in range(1, self.batch_size):
            prediction = tf.concat([prediction, get_max_conf_cell(self.logits[i, :, :, :],num_boxes)], 0)
        return prediction

    def get_logits(self):
        return self.logits  # , self.variables

    # dumb function
    def _zero_cond(self):
        zero = tf.constant(0, dtype=tf.float32)
        return zero, zero, zero

    def _present_object_cost(self, h, y, num_boxes, lambda_coord=1.0):
        iou = IoU_parallel(y, h)
        max_IoU_idx = tf.argmax(iou)
        if num_boxes == 1:
            h_max = h[max_IoU_idx[0], 0, :4]
        else:
            h_max = h[max_IoU_idx[0], max_IoU_idx[1], :4]
        y_max = y[max_IoU_idx[0], :4]
        regression_loss = lambda_coord * tf.reduce_sum(tf.math.add(tf.squared_difference(h_max[0], y_max[0]),
                                                                   tf.squared_difference(h_max[1], y_max[1])))
        regression_loss += lambda_coord * tf.reduce_sum(tf.math.add(tf.squared_difference(tf.sqrt(h_max[2]),
                                                                                          tf.sqrt(y_max[2])),
                                                                    tf.squared_difference(tf.sqrt(h_max[3]),
                                                                                          tf.sqrt(y_max[3]))))
        y_tiled = repeat_tensor(y[:, 4], tf.shape(h[:, :, 4])[1])
        confidence_loss = tf.reduce_sum(tf.squared_difference(h[:, :, 4], y_tiled))
        return confidence_loss, regression_loss, tf.reduce_mean(iou)

    # ignoring classification loss b/c only one class
    # function takes about 2.5 minutes when IoU not in parallel
    # and takes about 1.5 when IoU in parallel
    def _get_cost(self, logits, num_boxes, num_cells, lambda_coord=1.0, lambda_noobj=0.5):
        regression_loss = 0  # tf.Variable(tf.zeros([], dtype=np.float32), name='regression_loss')#0
        classification_loss = 0  # tf.Variable(tf.zeros([], dtype=np.float32), name='classification_loss')#0
        confidence_loss = 0  # tf.Variable(tf.zeros([], dtype=np.float32), name='confidence_loss')#0
        avg_IoU = 0
        for i in range(self.batch_size):
            #    ''' # <- COMMENT OUT THIS TRIPLE-QUOTE AND THE NEXT TRIPLE-QUOTE TO RUN IN PARALLEL
            y_reshaped = tf.reshape(self.y[i, :, :, :], [-1, 5])
            h_reshaped = tf.reshape(logits[i, :, :, :], [-1, num_boxes, 5])
            h_w, h_wo, y_w, y_wo = separate_trues(h_reshaped, y_reshaped)  # separate into groups of object, no object
            confidence_loss -= lambda_noobj * tf.reduce_sum(h_wo[:, :, 4])
            cl, rl, avg_iou = tf.cond(tf.shape(h_w)[0] > 0,
                                      lambda: self._present_object_cost(h_w, y_w, num_boxes, lambda_coord),
                                      lambda: self._zero_cond())
            confidence_loss += cl
            regression_loss += rl
            avg_IoU += avg_iou
        return classification_loss + regression_loss + abs(confidence_loss)  # , avg_IoU / self.batch_size

    def predict(self, model_path, x_test):
        init = tf.global_variables_initializer()
        with tf.Session() as sess:
            lgts = sess.run(init)
            self.restore(sess, model_path)
            y_dummy = np.empty((1, self.num_cells, self.num_cells, 5))
            return sess.run(self.predicter, feed_dict={self.x: x_test, self.y: y_dummy, self.dropout: 1.0})

    def save(self, sess, model_path):
        saver = tf.train.Saver()
        return saver.save(sess, model_path)

    def restore(self, sess, model_path):
        ckpt = tf.train.get_checkpoint_state(model_path)
        if ckpt and ckpt.model_checkpoint_path:
            saver = tf.train.Saver()
            saver.restore(sess, ckpt.model_checkpoint_path)
            logging.info("Model restored from file: %s" % model_path)


class YoloTrainer(object):
    def __init__(self, model, batch_size=1, validation_batch_size=1, opt_kwargs={}):
        self.model = model
        self.batch_size = batch_size
        self.validation_batch_size = validation_batch_size
        self.opt_kwargs = opt_kwargs

    def _get_optimizer(self, global_step):
        learning_rate = self.opt_kwargs.pop("learning_rate", 0.0001)
        self.learning_rate_node = tf.Variable(learning_rate, name="learning_rate")
        optimizer = tf.train.AdamOptimizer(learning_rate=self.learning_rate_node, beta1=0.9, epsilon=1e-8,
                                           **self.opt_kwargs).minimize(self.model.cost, global_step=global_step)
        return optimizer

    def _initialize(self, output_path, restore, prediction_path):
        global_step = tf.Variable(0, name="global_step")
        tf.summary.scalar('loss', self.model.cost)
        # tf.summary.scalar('regression_accuracy', self.model.regression_accuracy)
        # TODO: accuracy metrics?
        self.optimizer = self._get_optimizer(global_step)
        tf.summary.scalar('learning_rate', self.learning_rate_node)
        self.summary_op = tf.summary.merge_all()

        init = tf.global_variables_initializer()

        self.prediction_path = prediction_path
        abs_prediction_path = os.path.abspath(self.prediction_path)
        output_path = os.path.abspath(output_path)
        if not restore:
            logging.info("Removing '{:}'".format(abs_prediction_path))
            shutil.rmtree(abs_prediction_path, ignore_errors=True)
            logging.info("Removing '{:}'".format(output_path))
            shutil.rmtree(output_path, ignore_errors=True)

        if not os.path.exists(abs_prediction_path):
            logging.info("Allocating '{:}'".format(abs_prediction_path))
            os.makedirs(abs_prediction_path)

        if not os.path.exists(output_path):
            logging.info("Allocating '{:}'".format(output_path))
            os.makedirs(output_path)

        return init

    def train(self, training_generator, validation_generator, total_validation_data, training_iters,
              restore_path, output_path, epochs=100, display_step=2, dropout=0.75, prediction_path='prediction',
              write_graph=False, restore=False):

        save_path = os.path.join(output_path, "model.ckpt")

        epoch_offset = 0
        try:
            epoch_file = open(output_path + "\\last_epoch.txt", "r")
            if restore:
                try:
                    epoch_offset = int(epoch_file.readline())
                except(ValueError):
                    epoch_offset = 0
            epoch_file.close()
        except(FileNotFoundError):
            print("Note: last_epoch.txt was not found. Assumed starting @ epoch 0")

        init = self._initialize(output_path, restore_path, prediction_path)

        validation_avg_losses = []
        training_avg_losses = []
        # no accuracies yet

        try:
            training_file = open(output_path + "\\training_data.txt", "r")
            validation_file = open(output_path + "\\validation_data.txt", "r")
            if restore:
                try:
                    training_avg_losses = [float(i) for i in training_file.readline()[1:-2].split(', ')]
                    # training_accuracies = [float(i) for i in training_file.readline()[1:-1].split(', ')]
                    validation_avg_losses = [float(i) for i in validation_file.readline()[1:-2].split(', ')]
                    # validation_accuracies = [float(i) for i in validation_file.readline()[1:-1].split(', ')]
                except(ValueError):
                    print("No prior training or validation data exists. Assuming new model")
            training_file.close()
            validation_file.close()
        except(FileNotFoundError):
            print("No prior training or validation data exists. Assuming new model")

        with tf.Session(config=config) as sess:
            # sess = tf_debug.LocalCLIDebugWrapperSession(sess)

            if write_graph:
                tf.train.write_graph(sess.graph_def, output_path, "graph.pb", False)

            sess.run(init)

            if restore:
                self.model.restore(sess, restore_path)
                #ckpt = tf.train.get_checkpoint_state(restore_path)
                #if ckpt and ckpt.model_checkpoint_path:
                #    self.model.restore(sess, ckpt.model_checkpoint_path)

            summary_writer = tf.summary.FileWriter(output_path, graph=sess.graph)

            # takes about 2.5 minutes to start after this logging when IoU in parallel
            # and more than 5 minutes when not in parallel
            logging.info("Start optimization")

            for epoch in range(epochs):
                total_loss = 0
                total_acc = 0
                for step in range((epoch * training_iters), ((epoch + 1) * training_iters)):
                    batch_x, batch_y = training_generator(self.batch_size)
                    _, loss, lr, gradients = sess.run(
                        (self.optimizer, self.model.cost, self.learning_rate_node, self.model.gradients_node),
                        feed_dict={self.model.x: batch_x, self.model.y: batch_y, self.model.dropout: dropout})
                    if step % display_step == 0:
                        self.output_minibatch_stats(sess, summary_writer, step, batch_x, batch_y)
                    total_loss += loss
                training_avg_losses.append(total_loss / training_iters)
                true_epoch = epoch + epoch_offset
                self.output_epoch_stats(true_epoch, total_loss, training_iters, lr)
                validation_avg_losses = self.validate(sess, total_validation_data, validation_generator,
                                                      validation_avg_losses)
            epoch_file = open(output_path + "\\last_epoch.txt", "w")
            epoch_file.write(str(true_epoch + 1))
            epoch_file.close()
            training_file = open(output_path + "\\training_data.txt", "w")
            training_file.write(str(training_avg_losses) + "\n")
            training_file.close()
            validation_file = open(output_path + "\\validation_data.txt", "w")
            validation_file.write(str(validation_avg_losses) + "\n")
            validation_file.close()
            save_path = self.model.save(sess, save_path)
        logging.info("Optimization Finished")
        return save_path

    def validate(self, sess, total_validation_data, validation_generator, validation_avg_losses):
        total_validation_loss = 0
        validation_iters = int(total_validation_data / self.validation_batch_size)
        last_batch_size = total_validation_data - (validation_iters * self.validation_batch_size)
        for i in range(0, validation_iters):
            test_x, test_y = validation_generator(self.validation_batch_size)
            loss = sess.run(self.model.cost,
                            feed_dict={self.model.x: test_x, self.model.y: test_y, self.model.dropout: 1.0})
            total_validation_loss += loss
        if last_batch_size != 0:
            test_x, test_y = validation_generator(last_batch_size)
            loss = sess.run(self.model.cost,
                            feed_dict={self.model.x: test_x, self.model.y: test_y, self.model.dropout: 1.0})
            total_validation_loss += loss
            validation_iters += 1
        validation_avg_losses.append(total_validation_loss / validation_iters)
        logging.info("Average validation loss= {:.4f}".format(total_validation_loss / validation_iters))
        return validation_avg_losses

    # TODO
    # def save_prediction_image(self, image, img_save_path, name, best_box=False, y=None):
    #    prediction = #self.model.predict(image) # need to add model_path
    #    convert_xywh_to_prediction_image(image, prediction, self.model.num_cells, img_save_path, name,
    #                                     best_box=best_box, true_boxes=y)

    def output_minibatch_stats(self, sess, summary_writer, step, batch_x, batch_y):
        summary_str, loss = sess.run([self.summary_op, self.model.cost],
                                     feed_dict={self.model.x: batch_x, self.model.y: batch_y,
                                                self.model.dropout: 1.0})
        summary_writer.add_summary(summary_str, step)
        summary_writer.flush()
        logging.info("Iter{:}, Minibatch Loss= {:.4f}".format(step, loss))

    def output_epoch_stats(self, epoch, total_loss, training_iters, lr):
        logging.info(
            "Epoch {:}, Average loss: {:.4f}, learning rate: {:.4f}".format(epoch, (total_loss / training_iters),
                                                                            lr))
