import matplotlib.pyplot as plt
import mne.io

def cleanSubplots(r, c, pad=0.05, axes=False):
    """
    Open a full-screen (r x c) matplotlib graph with minimal padding
    """
    f, ax = plt.subplots(r, c)
    if not axes:
        if r == 1 and c == 1:
            ax.get_xaxis().set_visible(False)
            ax.get_yaxis().set_visible(False)
        elif r == 1 or c == 1:
            for a in ax:
                a.get_xaxis().set_visible(False)
                a.get_yaxis().set_visible(False)
        else:
            for aRow in ax:
                for a in aRow:
                    a.get_xaxis().set_visible(False)
                    a.get_yaxis().set_visible(False)
    f.subplots_adjust(left=pad, right=1.0-pad, top=1.0-pad, bottom=pad, hspace=pad)
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
