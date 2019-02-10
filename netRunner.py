import tensorflow as tf
import numpy as np
from generator import Generator
from oneHotClasses import OneHotNetwork, OneHotNetworkTrainer

TRAIN_CSV_PATH = "D:/PCImages/train.csv"
VALIDATION_CSV_PATH = "D:/PCImages/validation.csv"

OUTPUT_PATH = "C://Users//Nick Nagy//Desktop//Python//Capstone"
RESTORE_PATH = OUTPUT_PATH

train_batch_size = 10
validation_batch_size = 10

learning_rate = 0.0001

train_generator = Generator(TRAIN_CSV_PATH)
validation_generator = Generator(VALIDATION_CSV_PATH)

epochs = 100
training_iters = int(train_generator.length() / train_batch_size) + int(train_generator.length()%train_batch_size > 0)

vgg16 = OneHotNetwork(model="vgg", layers=16)

vgg16_trainer = OneHotNetworkTrainer(vgg16, batch_size=train_batch_size, validation_batch_size=validation_batch_size,
                                     opt_kwargs=dict(learning_rate=learning_rate))
vgg16_trainer.train(train_generator, validation_generator, validation_generator.length(), RESTORE_PATH, OUTPUT_PATH,
                    epochs=epochs, training_iters=training_iters)
