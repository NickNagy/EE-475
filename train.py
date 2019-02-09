import tensorflow as tf
from backboneNetworks import vgg, resnet
import os
from matplotlib import pyplot as plt
import logging

config = tf.ConfigProto()
config.gpu_options.allow_growth = True

class OneHotNetwork(object):
    def __init__(self, model="vgg", layers=16):
        tf.reset_default_graph()
        self.x = tf.placeholder("float", shape=[None, None, None, 1], name="x")
        self.y = tf.placeholder("float", shape=[None, 1, 1, 1], name="y")

        # TODO: lambda function?
        if model == "vgg":
            logits, self.variables = vgg(self.x, num_layers=layers)
        else:
            logits, self.variables = resnet(self.x, num_layers=layers)

        self.cost = self._get_cost()

        self.gradients_node = tf.gradients(self.cost, self.variables)

        with tf.name_scope("results"):
            self.predicter = tf.argmax(logits)
            self.accuracy = tf.reduce_mean(tf.equal(self.logits, self.y))

    # TODO: look into loss functions for VGG & Resnet
    def _get_cost(self, logits):
        with tf.name_scope("cost"):
            return tf.nn.softmax_cross_entropy_with_logits(logits, self.y)

    def predict(self, model_path, x_test):
        init = tf.global_variables_initializer()
        with tf.Session() as sess:
            lgts = sess.run(init)
            self.restore(sess, model_path)
            y_dummy = np.empty((1, 1, 1, 1))
            return sess.run(self.predicter, feed_dict={self.x: x_test, self.y: y_dummy})

    def save(self, sess, model_path):
        saver = tf.train.Saver()
        return saver.save(sess, model_path)

    def restore(self, sess, model_path):
        saver = tf.train.Saver()
        saver.restore(sess, model_path)
        logging.info("Model restored from file: %s" % model_path)

class OneHotNetworkTrainer(object):
    def __init__(self, model, batch_size=1, validation_batch_size=1, opt_kwargs={}):
        self.model = model
        self.batch_size = batch_size
        self.validation_batch_size = validation_batch_size
        self.opt_kwargs = opt_kwargs

    def _get_optimizer(self, global_step):
        learning_rate = self.opt_kwargs.pop("learning_rate", 0.001)
        self.learning_rate_node = tf.Variable(learning_rate, name="learning_rate")
        optimizer = tf.train.AdamOptimizer(learning_rate=self.learning_rate_node, beta1=0.9, epsilon=1e-8,
                                           **self.opt_kwargs).minimize(self.net.cost, global_step=global_step)
        return optimizer

    def _initialize(self, output_path, restore, prediction_path):
        global_step = tf.Variable(0, name="global_step")
        tf.summary.scalar('loss', self.net.cost)
        tf.summary.scalar('accuracy', self.net.accuracy)
        tf.summary.scalar('learning_rate', self.learning_rate_node)
        self.optimizer = self._get_optimizer(global_step)
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

    def train(self, train_generator, validation_generator, total_validation_data, restore_path, output_path,
              training_iters=10, epochs=100, prediction_path = 'prediction'):
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

        init = self._initialize(output_path, restore, prediction_path)

        validation_avg_losses = []
        training_avg_losses = []
        training_accuracies = []
        validation_accuracies = []

        try:
            training_file = open(output_path + "\\training_data.txt", "r")
            validation_file = open(output_path + "\\validation_data.txt", "r")
            if restore:
                try:
                    # TODO: better way?
                    training_avg_losses = [float(i) for i in training_file.readline()[1:-2].split(', ')]
                    training_accuracies = [float(i) for i in training_file.readline()[1:-1].split(', ')]
                    validation_avg_losses = [float(i) for i in validation_file.readline()[1:-2].split(', ')]
                    validation_accuracies = [float(i) for i in validation_file.readline()[1:-1].split(', ')]
                except(ValueError):
                    print("No prior training or validation data exists. Assuming new model")
            training_file.close()
            validation_file.close()
        except(FileNotFoundError):
            print("No prior training or validation data exists. Assuming new model")

        with tf.Session(config=config) as sess:
            if write_graph:
                tf.train.write_graph(sess.graph_def, output_path, "graph.pb", False)

            sess.run(init)

            if restore:
                ckpt = tf.train.get_checkpoint_state(restore_path)
                if ckpt and ckpt.model_checkpoint_path:
                    self.net.restore(sess, ckpt.model_checkpoint_path)

            summary_writer = tf.summary.FileWriter(output_path, graph=sess.graph)
            loggig.info("Start optimization")

            for epoch in range(epochs):
                total_loss = 0
                total_acc = 0
                for step in range((epoch*training_iters), ((epoch+1)*training_iters)):
                    batch_x, batch_y = train_generator(self.batch_size)
                    _, loss, lr, gradients = sess.run(
                        (self.optimizer, self.model.cost, self.learning_rate_node, self.model.graients_node),
                        feed_dict = {self.model.x: batch_x, self.model.y: batch_y})
                    if step%display_step == 0:
                        acc = self.output_minibatch_stats(sess, summary_writer, step, batch_x, batch_y)
                    total_loss += loss
                    total_acc += acc
                training_avg_losses.append(total_loss / training_iters)
                training_accuracies.append(total_acc / training_iters)
                true_epoch = epoch+epoch_offset
                self.output_epoch_stats(true_epoch, total_loss, training_iters, lr)
                validation_avg_losses, validation_accuracies = self.validate(sess, total_validation_data,
                                                                                validation_generator,
                                                                                validation_avg_losses,
                                                                                validation_accuracies)
                epoch_file = open(output_path + "\\last_epoch.txt", "w")
                epoch_file.write(str(true_epoch + 1))
                epoch_file.close()
                # TODO: find more efficient way
                training_file = open(output_path + "\\training_data.txt", "w")
                training_file.write(str(training_avg_losses) + "\n")
                training_file.write(str(training_accuracies))
                training_file.close()
                validation_file = open(output_path + "\\validation_data.txt", "w")
                validation_file.write(str(validation_avg_losses) + "\n")
                validation_file.write(str(validation_accuracies))
                validation_file.close()
                save_path = self.net.save(sess, save_path)
            logging.info("Optimization Finished")

            return save_path

    def validate(self, sess, total_validation_data, validation_generator, validation_avg_losses, validation_accuracies):
        total_validation_loss = 0
        total_validation_acc = 0
        validation_iters = int(total_validation_data / self.validation_batch_size)
        last_batch_size = total_validation_data - (validation_iters * self.validation_batch_size)

        for i in range(0, validation_iters):
            test_x ,test_y = validation_generator(self.validation_batch_size)
            loss, accuracy = sess.run((self.model.cost, self.model.accuracy), feed_dict={self.model.x: test_x,
                                                                                         self.model.y: test_y})
            total_validation_loss += loss
            total_validation_acc += accuracy
        if last_batch_size != 0:
            test_x, test_y = validation_generator(last_batch_size)
            loss, accuracy = sess.run((self.model.cost, self.model.accuracy), feed_dict={self.model.x: test_x,
                                                                                         self.model.y:test_y})
            total_validation_loss += loss
            total_validation_acc += accuracy
            validation_iters += 1
        validation_avg_losses.append(total_validation_loss / validation_iters)
        validation_accuracies.append(total_validation_acc / validation_iters)

        logging.info("Average validation loss= {:.4f}".format(total_validation_loss / validation_iters))
        return validation_avg_losses, validation_accuracies

    def output_minibatch_stats(self, sess, summary_writer, step, batch_x, batch_y):
        summary_str, loss, acc, predictions = sess.run([self.summary_op, self.net.cost, self.net.accuracy,
                                                        self.net.predicter],
                                                       feed_dict={self.net.x: batch_x, self.net.y: batch_y})
        summary_writer.add_summary(summary_str, step)
        summary_writer.flush()
        logging.info("Iter{:}, Minibatch Loss= {:.4f}, Training Accuary= {:.4f}".format(step, loss, acc))
        return acc

    def output_epoch_stats(self, epoch, total_loss, training_iters, lr):
        logging.info("Epoch {:}, Average loss: {:4f}, learning rate: {:.4f}".format(epoch, (total_loss/training_iters),
                                                                                    lr))