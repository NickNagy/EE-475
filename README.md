# EE-475
## Embedded Systems Capstone Project ##

## A Note from Nick Nagy ##

Our main goal with this capstone project was to create an interactive embedded device that uses machine learning / computer vision to recognize the user's index finger for the basis of user selections. In other words, we were trying to make a device that someone could interact with, without needing to touch the screen physically.

Part of the challenge for me was to deeply familiarize myself with convolutional networks, by implementing them from scratch. I originally tried implementing RetinaNet, INCLUDING training VGG-16 from scratch. However, because our data is reduced to a binary classification problem, the loss evaluation for VGG-16 was poor, and I was concerned that even if we replaced it with a more appropriate backbone, that moving forward with the rest of the RetinaNet architecture would be too difficult and not promising enough given our time constraints. Additionally, because our end goal was to have this on a Raspberry Pi in a NumPy basis rather than Tensorflow, we wanted an architecture that was much smaller scale.

We changed our network to a smaller implementation of the original YOLO network. Training has not been great, for a multitude of possible reasons (very small data sets, no implemented augmentations yet, improper loss function, binary problem, etc). However, I am proud of the work I've dedicated to this project so far, and have no plans to abandon it.

Moving forward after the quarter ends I have a few next steps I plan to try. I want to get far more data + augmenetations, and see if it improves training. If not, I will look into alternative architectures or see how training runs on a different user's implementation. Also, I want to branch out and try other possible approaches to finger recognition, and see which is perhaps the best fit for this overall design.

~ Nick Nagy 3/16/19

## Summary of Files ##

**ArduinoImage**: sets up Serial communication w/Arduino for camera capture. Can save image data in real-time.

**PCImage**: same as Arduino Image but uses video capture on PC.

**anchorTesting**: Jupyter Notebook, testing out different implementations for generating bounding box predictions from an image.

**backboneNetworks**: VGG and ResNet architectures. To be used as backbones for Retinanet, when implemented properly.

**dataLabelingScript**: program for labeling box regions for our image data.

**draw**: Windows-compatible script for using camera and mouse to interact using a trained network.

**generator**: generates training data from csv file. Callable.

**layers**: pretty standard TF layer methods.

**lossTest**: debugging methods for testing other functions, files, etc

**main**: PIC18F452 serial communication.

**netRuner**: script for training a network.

**numpyNet**: trained model running in numpy. Currently buggy.

**oneHotClasses**: one-hot network class and trainer class.

**retinanetClasses**: retinanet class w/ loss functions, etc, and trainer class.

**retinanetStructure**: functions to help define model structure, fpn, anchor boxes, etc.

**utils**: associated utility functions, such as image summaries.

**yoloStructure**: functions to help define YOLO structure

**yoloClasses**: YOLO class w/loss functions, etc, and trainer class.

## General Steps to Using the Above Python Files ##

1) Use PCImage, ArduinoImage or a similar script for creating raw images using video capture.

2) Use dataLabelingScript to draw coordinate boxes around finger tips in each raw image and create your database(s).

3) Use / modify netRunner to train a network on your database(s).

...

4) Once you have a trained network, there are some practice real-time functions in netRunner, **OR**, if you're running on a Windows computer, you can use draw.py to try controlling your mouse with your finger!
