import matplotlib.pyplot as plt
import mne.io
import numpy as np
# from numpy import corrcoef
# from matplotlib.pyplot import pcolor, show, colorbar, xticks, yticks

def cleanSubplots(r, c, pad=0.05, axes=False):
    """
    Open a full-screen (r x c) matplotlib graph with minimal padding
    """
    f, ax = plt.subplots(r, c)
    f.subplots_adjust(left=pad, right=1.0-pad, top=1.0-pad, bottom=pad, hspace=pad*2)
    try:
        plt.get_current_fig_manager().window.showMaximized()
    except AttributeError:
        pass # Can't maximize, sorry :(
    return ax

def showEdfSignal(edfPath):
    """
    Utility to load edf data and show the signals.
    """
    print("Loading %s..." % edfPath)
    raw = mne.io.read_raw_edf(edfPath, preload=True)
    raw.plot(block=True)

def correlationMatrix(corr):
    """
    Draws a correlation matrix visually.
    """
    # R = np.corrcoef(corr)
    plt.pcolor(corr, cmap='jet')
    plt.colorbar()
    plt.show()


# Utility to convert e.g. T013_D001_V00_2017_05_16_Emily-Resting-30Hzfilt.edf to Emily-Resting
def shortName(longName):
    first = longName.find('-')
    return longName[longName.rfind('_') + 1:longName[first+1:].find('-') + first + 1]
