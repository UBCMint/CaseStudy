# Based off the work from Uberi:
# https://gist.github.com/Uberi/283a13b8a71a46fb4dc8

import matplotlib.pyplot as plt
import numpy as np
from collections import deque

# Scrolling graph of values, with additional connected status
class LiveGraph:
    def __init__(self, ax, title, maxEntries = 100, minY = -2.0, maxY = 2.0):
        self.ax = ax
        self.isGood = False
        self.yValues = deque(maxlen = maxEntries)
        self.title = title

        # Set up graph
        self.lineplot, = ax.plot([], [], "b+-")
        self.ax.set_title(self.title)
        self.ax.set_xlim(0, maxEntries - 1 + 1e-9)
        self.ax.set_ylim(minY, maxY)

    def setGood(self, isGood):
        """
        Update the 'good' status of the graph, changing visual appearance too
        """
        self.isGood = isGood
        if self.isGood:
            self.ax.set_title(self.title)
            self.ax.title.set_color('black')
        else:
            self.ax.set_title(self.title + ' ** dc')
            self.ax.title.set_color('red')

    def add(self, y):
        """
        Adds the most recent y value onto the graph, and scrolls it into view.
        """
        if self.isGood:
            self.yValues.append(y)
        else:
            self.yValues.append(0.)
        self.lineplot.set_data(np.arange(0, len(self.yValues)), self.yValues)
