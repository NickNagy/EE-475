import numpy as np
from random import shuffle
from PIL import Image

class Generator(object):

    def __init__(self, file_path, one_hot=True, shuffle_data=True):
        file = open(file_path, "r")
        image_path, x1, y1, x2, y2, label = file.readline().split(',')
        coordinates = np.array([None, None, None, None])
        if x1 != '':
            coordinates = np.array([int(x1), int(y1), int(x2), int(y2)])
        self.data_list = []
        self.idx = 0
        self.shuffle_data = shuffle_data
        self.one_hot = one_hot
        # issue if used on a multi-class problem
        while True:
            try:
                while True:
                    new_image_path, x1, y1, x2, y2, new_label = file.readline().split(',')
                    if new_image_path != image_path:
                        self.data_list.append((image_path, coordinates, label))
                        if x1 != '':
                            coordinates = np.array([int(x1), int(y1), int(x2), int(y2)])
                        image_path = new_image_path
                        label = new_label
                        break
                    if x1 != '':
                        coordinates = np.append(coordinates, [[int(x1), int(y1), int(x2), int(y2)]], axis=0)
            except ValueError:
                break
        file.close()

    def length(self):
        return len(self.data_list)

    def _load_data_and_label(self):
        data, label = self._next_data()
        labels = np.array([~label, label])
        return data.reshape(1, data.shape[0], data.shape[1], 1), labels.reshape(1,1,1,2)

    def __call__(self, n):
        #if not self.one_hot:
        #    data, boxes, labels = self._load_data_and_label()
        #    B = np.zeros((n, ))
        data, labels = self._load_data_and_label()
        nx = data.shape[1]
        ny = data.shape[2]
        X = np.zeros((n, nx, ny, 1))
        Y = np.zeros((n, 1, 1, 2))
        X[0] = data
        Y[0] = labels
        for i in range(1, n):
            data, labels = self._load_data_and_label()
            X[i] = data
            Y[i] = labels
        return X,Y

    def _load_image(self, path, dtype=np.float32):
        return np.array(Image.open(path), dtype)

    def _cycle(self):
        self.idx += 1
        if self.idx >= len(self.data_list):
            self.idx = 0
            if self.shuffle_data:
                shuffle(self.data_list)

    def _next_data(self):
        self._cycle()
        image_path = self.data_list[self.idx][0]
        image = self._load_image(image_path, np.float32)
        label = int(self.data_list[self.idx][2])
        if not self.one_hot:
            boxes = self.data_list[self.idx][1]
            return image, boxes, label
        return image, label
