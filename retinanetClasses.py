import tensorflow as tf
from collections import OrderedDict
from retinanetStructure import retinanet

def IoU(true, pred):
    pred_x1 = pred[:,0]
    pred_y1 = pred[:,1]
    pred_x2 = pred[:,2]
    pred_y2 = pred[:,3]
    true_x1 = true[:,0]
    true_y1 = true[:,1]
    true_x2 = true[:,2]
    true_y2 = true[:,3]
    xA = tf.math.maximum(pred_x1, tf.transpose(true_x1))
    yA = tf.math.maximum(pred_y1, tf.transpose(true_y1))
    xB = tf.math.minimum(pred_x2, tf.transpose(true_x2))
    yB = tf.math.minimum(pred_y2, tf.transpose(true_y2))
    inter_area = tf.maximum((xB-xA+1),0)*tf.maximum((yB-yA+1),0)
    pred_area = (pred_x2-pred_x1+1)*(pred_y2-pred_y1+1)
    true_area = (true_x2-true_x1+1)*(true_y2-true_y1+1)
    return tf.reduce_mean(inter_area / (pred_area + tf.transpose(true_area)))

class RetinaNet(object):
    def __init__(self, backbone="vgg", backbone_layers=16):
        tf.reset_default_graph()

        self.x = tf.placeholder("float", [None, None, None, 1], name="x")
        self.y = tf.placeholder("int", [None, 1, 5, 1], name="y") # unsure of y-dimension

        self.pyramids, self.shared_variables = retinanet(self.x, backbone, backbone_layers)

    def _focal(self):

    def _smooth_L1(self):