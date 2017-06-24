import matplotlib.pyplot as plt
import mne.io

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
    print "Loading %s..." % edfPath
    raw = mne.io.read_raw_edf(edfPath, preload=True)
    raw.plot(block=True)
