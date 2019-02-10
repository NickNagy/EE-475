import tensorflow as tf
import numpy as np
from generator import Generator
from OneHotClasses import OneHotNetwork, OneHotNetworkTrainer

TRAIN_CSV_PATH = "D:/PCImages/data.csv"
VALIDATION_CSV_PATH = TRAIN_CSV_PATH#""

OUTPUT_PATH = "C://Users//Nick Nagy//Desktop//Capstone"
RESTORE_PATH = OUTPUT_PATH

train_batch_size = 1
validation_batch_size = 1

train_generator = Generator(TRAIN_CSV_PATH)
validation_generator = Generator(VALIDATION_CSV_PATH)

vgg16 = OneHotNetwork(model="vgg", layers=16)

vgg16_trainer = OneHotNetworkTrainer(vgg16, batch_size=train_batch_size, validation_batch_size=validation_batch_size)
vgg16_trainer.train(train_generator, validation_generator, validation_generator.length(), RESTORE_PATH, OUTPUT_PATH)
