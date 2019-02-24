"""
Generator class for one-hot encoded convolutional neural network and/or SSD networks (the latter to be implemented)

Note: this has only been tested on two-class problems.

- Nick
"""

import numpy as np
from random import shuffle
from PIL import Image


# TODO: only works for 2-class problem right now
def convert_xyxy_to_xywh(img, coords, num_cells):
    # returns a 3d array of shape num_cells*num_cells*4, where each index (i,j,:) corresponds to a cell space in img
    # if coordinates of an object fall in a cell space, then cell_array(i,j,:) = (x, y, width, height, label) of the
    # object, where x and y are the centerpoints of the ground truth box. All four values are normalized wrt the cell
    # space
    w, h = img.shape
    cell_w = w / num_cells
    cell_h = h / num_cells
    cell_array = np.zeros((num_cells, num_cells, 5))
    for i in range(len(coords)):
        x1, y1, x2, y2, label = coords[i]
        x_center = (x1 + x2) / 2
        y_center = (y1 + y2) / 2
        cell_x = int(x_center / cell_w)
        cell_y = int(y_center / cell_h)
        if cell_x == 0:
            box_x = x_center
        else:
            box_x = (x_center - cell_w * cell_x) / (cell_w * cell_x)
        if cell_y == 0:
            box_y = y_center
        else:
            box_y = (y_center - cell_h * cell_y) / (cell_h * cell_y)
        box_w = (x2 - x1) / cell_w
        box_h = (y2 - y1) / cell_h
        cell_array[cell_x, cell_y, :] = (box_x, box_y, box_w, box_h, label)
        # coords[i] = (box_x, box_y, box_w, box_h)
    return img, cell_array

# NOTE: this only works for 2-class problem right now
class Generator(object):
    def __init__(self, file_path, one_hot=True, shuffle_data=True, xywh=True, num_cells=7):
        """
        Converts data from a CSV file into a data list of format [(image, [x1, y1, x2, y2], class), ...]
        :param file_path: path to csv file w/ data in format: path_to_img, x1, y1, x2, y2, class
        :param one_hot: bool, True if coordinates data should be ignored
        :param shuffle_data: bool, True if the order of data list should be shuffled
        :param xywh: bool, only necessary if one_hot is False. True if coordinates should be in (x_center, y_center, width, height) form
        :param num_cells: number of cells image should be divided into. Only necessary if one_hot is False
        """
        file = open(file_path, "r")
        image_path, x1, y1, x2, y2, label = file.readline().split(',')
        coordinates = np.array([None, None, None, None, None])
        if not self.one_hot and x1 != '':
            coordinates = np.array([int(x1), int(y1), int(x2), int(y2), int(label)])
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
                        if not self.one_hot:
                            if xywh:
                                image_path, coordinates = convert_xyxy_to_xywh(image_path, coordinates, num_cells)
                            self.data_list.append((image_path, coordinates))  # label stored in coordinates
                        else:
                            self.data_list.append((image_path, label))
                        if not self.one_hot and x1 != '':
                            coordinates = np.array([int(x1), int(y1), int(x2), int(y2), int(new_label)])
                        image_path = new_image_path
                        label = new_label
                        break
                    if not self.one_hot and x1 != '':
                        coordinates = np.append(coordinates, [[int(x1), int(y1), int(x2), int(y2), int(new_label)]], axis=0)
            except ValueError:
                break
        file.close()
        if self.shuffle_data:
            shuffle(self.data_list)

    def length(self):
        return len(self.data_list)

    def _load_data_and_label(self):
        data, labels = self._next_data()
        if not self.one_hot:
            return data.reshape(1, data.shape[0], data.shape[1], 1), labels.reshape(1, labels.shape[0],
                                                                                       labels.shape[1], labels.shape[2])
        return data.reshape(1, data.shape[0], data.shape[1], 1), labels

    def __call__(self, n):
        data, labels = self._load_data_and_label()
        nx = data.shape[1]
        ny = data.shape[2]
        X = np.zeros((n, nx, ny, 1))
        Y_shape = n
        if not self.one_hot:
            Y_shape = (n, labels.shape[0], labels.shape[1], labels.shape[2])
        Y = np.zeros((Y_shape))
        X[0] = data
        Y[0] = labels
        for i in range(1, n):
            data, labels = self._load_data_and_label()
            X[i] = data
            Y[i] = labels
        return X, Y

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
        if not self.one_hot:
            labels = self.data_list[self.idx][1]
            return image, labels
        label = int(self.data_list[self.idx][1])
        return image, label
