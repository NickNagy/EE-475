# EE-475
Embedded Systems Capstone Project

**ArduinoImage**: sets up Serial communication w/Arduino for camera capture. Can save image data in real-time.

**SignalReader**: signal storing, FFT, serial communication with PIC18F452.

**anchors**: module for anchor functions (SSD).

**anchorTesting**: Jupyter Notebook, testing out different implementations for generating bounding box predictions from an image.

**backboneNetworks**: VGG and ResNet architectures. To be used as backbones for Retinanet, when implemented properly.

**boundingBox**: program for labeling box regions for our image data.

**generator**: generates training data from csv file. Callable.

**layers**: pretty standard TF layer methods.

**main**: PIC18F452 serial communication.

**train**: one-hot network class and trainer class.
