# Draws histogram of all tbr, rather than graph of last N

import matplotlib.pyplot as plt
import numpy as np
from collections import deque

# Scrolling graph of values, with additional connected status
class LiveHist:
    def __init__(self, ax, title, segments = 20, minX = -2.0, maxX = 2.0):
        self.ax = ax
        self.title = title
        self.segments = segments
        self.minX = minX
        self.maxX = maxX
        self.isGood = False

        # Precalculate bucket positions and initialize counts to empty.
        segWidth = (maxX - minX) / segments
        self.xs = minX + (np.arange(0, segments) + 0.5) * segWidth
        self.counts = np.zeros(segments)

        # Set up graph
        self.lineplot, = ax.plot(self.xs, self.counts, "b+-")
        self.ax.set_title(self.title)
        self.ax.set_xlim(minX, maxX)
        self.ax.set_autoscaley_on(True)

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

    def add(self, value):
        """
        Adds the most recent y value onto the graph, adding it to the right bucket
        """
        if not self.isGood:
            return

        # Convert value to bucket it lies in.
        if value < self.minX:
            bucket = 0
        elif value >= self.maxX:
            bucket = self.segments - 1
        else:
            bucket = int(self.segments * (value - self.minX) / (self.maxX - self.minX))
        self.counts[bucket] += 1

        self.lineplot.set_data(self.xs, self.counts)
        self.ax.relim()
        self.ax.autoscale_view() # rescale the y-axis
