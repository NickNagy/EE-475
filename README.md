# EE-475
Embedded Systems Capstone Project

**ArduinoImage**: sets up Serial communication w/Arduino for camera capture. Can save image data in real-time.

**PCImage**: same as Arduino Image but uses video capture on PC.

**SignalReader**: signal storing, FFT, serial communication with PIC18F452.

**anchors**: module for anchor functions (SSD).

**anchorTesting**: Jupyter Notebook, testing out different implementations for generating bounding box predictions from an image.

**backboneNetworks**: VGG and ResNet architectures. To be used as backbones for Retinanet, when implemented properly.

**dataLabelingScript**: program for labeling box regions for our image data.

**generator**: generates training data from csv file. Callable.

**layers**: pretty standard TF layer methods.

**main**: PIC18F452 serial communication.

**netRuner**: script for training a network.

**oneHotClasses**: one-hot network class and trainer class.

## General Steps to Using the Above Python Files ##

1) Use PCImage, ArduinoImage or a similar script for creating raw images using video capture.

2) Use dataLabelingScript to draw coordinate boxes around finger tips in each raw image.

3) Use / modify netRunner to train a network on your data.
