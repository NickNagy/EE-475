# -*- coding: utf-8 -*-
"""
Created on Wed Jan 23 17:08:39 2019

@author: Nick Nagy
"""

import tensorflow as tf
import numpy as np
from backboneNetworks import vgg, resnet
from layers import weight, conv2d

def create_anchors(backbone_convs):
    # backbone_convs: a dictionary of convolutional layers
    anchor_layers = [backbone_convs[layer] for layer in backbone_convs.keys() if '_3' in layer]
    
    for layer in anchor_layers:
        w,h = layer.shape[1][2]
        