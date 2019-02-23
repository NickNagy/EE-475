import tensorflow as tf

# from: https://github.com/jakeret/tf_unet/tree/master/tf_unet
def get_image_summary(img):
    V = tf.slice(img, (0, 0, 0, 0), (1,-1,-1,1))
    V -= tf.reduce_min(V)
    V /= tf.reduce_max(V)
    V *= 255
    img_w = tf.shape(img)[1]
    img_h = tf.shape(img)[2]
    V = tf.reshape(V, tf.stack((img_w, img_h, 1)))
    V = tf.transpose(V, (2,0,1))
    V = tf.reshape(V, tf.stack((-1, img_w, img_h, 1)))
    return V