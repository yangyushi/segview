#!/usr/bin/env python3
import sys
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PyQt5.QtGui import QVector3D
from pyqtgraph.Qt import QtCore, QtGui
from matplotlib import cm


def index2position(image, metadata):
    indice = np.array(np.where(image > 0))
    ratio = np.array([[metadata['voxel_size_x'],
                       metadata['voxel_size_y'],
                       metadata['voxel_size_z']]]).T
    positions = indice * ratio[:len(indice)]
    return positions.T


def render_image(image, metadata, feature=None, alpha=1, feature_size=4):
    pg.mkQApp()
    view = gl.GLViewWidget()
    view.show()
    image_positions = index2position(image, metadata)
    view.opts['center'] = QVector3D(image_positions.T[0].flatten().max() / 2,
                                    image_positions.T[1].flatten().max() / 2,
                                    image_positions.T[2].flatten().max() / 2)  # rotation centre of the camera
    view.opts['distance'] = image_positions.flatten().max() * 2  # distance of the camera respect to the center
    image_color = np.zeros([len(image_positions), 4]) + np.array([0.1, 0.1, 1, alpha])
    point_image = gl.GLScatterPlotItem(pos=image_positions, color=image_color, pxMode=False)
    view.addItem(point_image)
    if not isinstance(feature, type(None)):
        feature = feature.T
        feature = np.array([feature[0] * metadata['voxel_size_x'],
                            feature[1] * metadata['voxel_size_y'],
                            feature[2] * metadata['voxel_size_z']])
        feature_size = np.ones(feature.shape[1]) * feature_size
        feature_color = np.zeros([feature.shape[1], 1]) + np.array([1, 0, 0, 1])
        point_feature = gl.GLScatterPlotItem(pos=feature.T, color=feature_color, size=feature_size)
        view.addItem(point_feature)
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


def render_label(labels, metadata, alpha=0.01):
    """
    labels.shape: (x_size, y_size, z_size)
    """
    pg.mkQApp()
    view = gl.GLViewWidget()
    view.show()
    label_positions = index2position(labels, metadata)
    view.opts['center'] = QVector3D(label_positions.T[0].flatten().max() / 2,
                                    label_positions.T[1].flatten().max() / 2,
                                    label_positions.T[2].flatten().max() / 2)  # rotation centre of the camera
    view.opts['distance'] = label_positions.flatten().max() * 2  # distance of the camera respect to the center
    label_color = np.array(label_to_rgba(labels, alpha))
    point_label = gl.GLScatterPlotItem(pos=label_positions, color=label_color, pxMode=False)
    view.addItem(point_label)
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


def refresh_scatter(plot, feature, upper, lower, **kargs):
    plot.clear()
    scatter = [(p[0], p[1]) for p in feature.T if (p[2] < upper and p[2] > lower)]
    plot.setData(pos=scatter, **kargs)


def refresh_image(canvas, new_image, z):
    canvas.clear()
    canvas.setImage(new_image[z])


def annotate_feature(image, feature, feature_size=4):
    image = np.moveaxis(image, -1, 0)  # x,y,z ---> z,x,y
    pg.mkQApp()
    window = pg.GraphicsLayoutWidget()
    p1 = window.addPlot(row=1, col=0, rowspan=3)
    p1.setPreferredHeight(1)
    p2 = window.addPlot(row=4, col=0, rowspane=1)
    p2.setXRange(0, len(image))
    p2.getViewBox().setMouseEnabled(0, 0)  # disable resize using mouse
    vline = pg.InfiniteLine(angle=90, movable=True, pen=pg.mkPen(cosmetic=False, width=0.1, color='y'))  # vertical line
    vline.setBounds([1, image.shape[0]])
    axis = pg.ScatterPlotItem()
    canvas = pg.ImageItem()
    region = pg.LinearRegionItem()
    region.setRegion([0, 2])
    p2.addItem(region)
    p2.addItem(vline)
    feature = feature.T

    def vline_update():
        z = int(vline.pos()[0])
        z = (z > 0) * z
        z = (z < len(image)) * z + ((z >= len(image)) * (len(image) - 1))
        refresh_image(canvas, image, z)
        lower, upper = region.getRegion()
        rw = upper - lower  # region_width
        region.setRegion([z - rw / 2, z + rw / 2])

    def region_update():
        lower, upper = region.getRegion()
        lower = int(lower)
        upper = int(upper)
        refresh_scatter(axis, feature, upper, lower,
                        size=10, brush=pg.mkBrush(color=(255, 0, 0, 255)))

    refresh_scatter(axis, feature, 0, 1, size=feature_size, brush=pg.mkBrush(color=(255, 0, 0, 255)))
    refresh_image(canvas, image, 1)

    vline.sigPositionChanged.connect(vline_update)
    vline.sigPositionChangeFinished.connect(vline_update)
    region.sigRegionChanged.connect(region_update)
    p1.addItem(axis)
    p1.addItem(canvas)
    canvas.setZValue(-100)
    window.resize(800, 800)
    window.show()
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


def refresh_label(plot, canvas, labels, z, show_com=False):
    """
    :param plot: a pyqtgraph.PlotItem instance
    :param canvas: a ImageItem instance, belonging to `plot`
    :param labels:  3D numpy array
    :param z:  the z stack value to show
    :param show_com: if show com on the plot, not recommonded
    :return:
    """
    canvas.clear()
    coms = []
    values = []
    canvas.setImage(label_to_2d_image(labels, z=z, alpha=0.5))
    if not show_com:
        return
    # get com of all labels
    projection = labels[z]
    for i in set(projection[projection > 0].ravel()):
        xy = np.where(projection == i)
        if xy:
            coms.append(np.average(xy, axis=1))
            values.append(str(i))
    for item in plot.items:  # remove previous label value
        if type(item) == pg.TextItem:
            plot.removeItem(item)
    for value, (x, y) in zip(values, coms):
        html = '<font size="12" color="white">%s</font>' % value
        text = pg.TextItem(html=html)
        text.setPos(x, y)
        plot.addItem(text)


def annotate_label(image, labels):
    image = np.moveaxis(image, -1, 0)  # x,y,z ---> z,x,y
    labels = np.moveaxis(labels, -1, 0)  # x,y,z ---> z,x,y
    # create canvas
    pg.mkQApp()
    window = pg.GraphicsLayoutWidget()
    p1 = window.addPlot(row=1, col=0, rowspan=3)
    p1.setPreferredHeight(1)
    p2 = window.addPlot(row=4, col=0, rowspane=1)
    p2.getViewBox().setMouseEnabled(0, 0)  # disable resize using mouse
    p2.setXRange(0, len(image))
    vline = pg.InfiniteLine(angle=90, movable=True, pen=pg.mkPen(cosmetic=False, width=0.1, color='y'))  # vertical line
    vline.setBounds([0, image.shape[0]])
    p2.addItem(vline)
    canvas_image = pg.ImageItem()
    canvas_label = pg.ImageItem()

    def vline_update():
        z_max = labels.shape[0]
        z = int(vline.getXPos())
        z = (z > 0) * z
        z = (z < z_max) * z + ((z >= z_max) * (z_max - 1))
        refresh_image(canvas_image, image, z)
        refresh_label(p1, canvas_label, labels, z)

    refresh_image(canvas_image, image, 1)
    refresh_label(p1, canvas_label, labels, 1)
    vline.sigPositionChanged.connect(vline_update)
    p1.addItem(canvas_image)
    p1.addItem(canvas_label)
    window.resize(640, 640)
    window.show()
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


def label_to_2d_image(labels, z='sum', alpha=0.5):
    """
    :param labels: (x, y, z), values are label values
    :return: (x, y, rgba)
    """

    if z == 'sum':
        labels_2d = labels.max(-1)
    else:
        labels_2d = labels[z, :, :]
    rgba = cm.tab10((labels_2d % 10 + 1) * (labels_2d > 0))
    rgba[:, :, -1] = alpha
    rgba[np.where(labels_2d == 0)] = np.zeros(4)
    return rgba


def label_to_rgba(labels, alpha=None):
    rgba = cm.tab10((labels % 10 + 1) * (labels > 0))
    if alpha:
        rgba[:, :, :, -1] = alpha
    rgba = rgba[np.where(labels > 0)]
    return rgba
