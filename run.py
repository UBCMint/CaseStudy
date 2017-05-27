import matplotlib.pyplot as plt
import mne.io
import numpy as np
import numpy.linalg
import scipy.signal
import mne.time_frequency

from multiprocessing import Pool

import viz

# >>> Parameters

# Channels to include in the analysis:
#          Fp1        F3        F7       FpZ       Fz      Fp2       F4        F8
PICKS = ['EEG 10', 'EEG 12', 'EEG 18', 'EEG 8', 'EEG 6', 'EEG 5', 'EEG 60', 'EEG 58'] # None = all non-bad channels.
# Although EEG 8 is technically AFz, but is the closest to FpZ

START_TIME_SEC = 1
END_TIME_SEC = 4.5 * 60

# Which frequency bands we want to calculate average power for.
BAND_FREQUENCIES = {
    'theta': [3.5, 7.5],
    'alpha': [7.5, 13.0],
    'beta': [13.0, 30.0],
}

# Take a rolling average of the last n values in a
def movingAverage(a, n=3) :
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

def calcBandPowers(raw):
    data = raw._data
    # Pick needed rows
    if PICKS is not None:
        pickIDs = mne.pick_types(raw.info, eeg=True, selection=PICKS)
        data = np.take(data, pickIDs, axis=0)

    # STFT for frequencies and powers
    freq, t, stft = scipy.signal.stft(data, fs=int(raw.info['sfreq']))
    powers = np.abs(stft)

    result = {}
    for bandID, bandHz in BAND_FREQUENCIES.iteritems():
        # Find the average power for the frequencies in the band
        fPick = np.logical_and(bandHz[0] < freq, freq < bandHz[1])
        meanPower = np.mean(powers[:, fPick, :], axis=(0, 1))
        result[bandID] = movingAverage(meanPower, 20)
    return result


def bandStrength(pathAndBads):
    """
    Given an array [path, badChannels], load the data and return power data for each channel
    """
    path, bads = pathAndBads[0], pathAndBads[1]
    raw = mne.io.read_raw_edf("data/" + path, preload=True)
    raw = raw.crop(tmin=START_TIME_SEC, tmax=END_TIME_SEC)
    raw.info['bads'] = bads

    result = calcBandPowers(raw)
    result['path'] = path
    return result


# Utility to convert e.g. T013_D001_V00_2017_05_16_Emily-Resting-30Hzfilt.edf to Emily-Resting
def shortName(longName):
    first = longName.find('-')
    return longName[longName.rfind('_')+1:longName[first+1:].find('-')+ first + 1]

def powerBandAnalysis(badMapping, nThreads=4):
    """
    Given a mapping path -> list of bad channels for that data, load all the path
    and calculate the frequency power plots for all desired bands.
    Does so multi-threaded to speed things up.
    """
    # Multithreaded mapping [path, bads] -> frequency powers
    p = Pool(processes=nThreads)
    badArray = []
    for path, bads in badMapping.iteritems():
        badArray.append([path, bads])
    badArray = sorted(badArray, key=lambda x: x[0]) # Sort by path.
    print badArray
    results = p.map(bandStrength, badArray)

    ax = viz.cleanSubplots(2, 2)
    ax[0, 0].set_title('theta')
    ax[1, 0].set_title('beta')
    ax[0, 1].set_title('TBR')
    ax[1, 1].set_title('TBR distribution')
    ax[1, 1].get_xaxis().set_visible(True)

    for i, result in enumerate(results):
        dot = '-' if i % 2 == 0 else '--' # line for Focus, dash for rest
        col = [(1,0,0), (0, 1, 0), (0, 0, 1), (.9, .7, 0), (.5, 0, .5), (0, .5, .5)][i // 2] # One colour per person
        t, b = result['theta'], result['beta']
        if i == 0:
            lt = len(t)
            ax[0,0].set_xlim([0, len(t)])
            ax[1,0].set_xlim([0, len(t)])

        ax[0, 0].plot(t, c=col, ls=dot)
        ax[1, 0].plot(b, c=col, ls=dot)
        ax[0, 1].plot(movingAverage(t / b, 20), c=col, ls=dot)
        # TBR distribution
        hist, edges = np.histogram(t / b, normed=True)
        ax[1, 1].plot(movingAverage(edges, 2), hist, c=col, ls=dot, label=shortName(result['path']))

    ax[1, 1].legend()
    plt.show()


if __name__ == '__main__':
    # """
    powerBandAnalysis({
        'T013_D001_V00_2017_05_16_Emily-Resting-30Hzfilt.edf': ['STI 014', 'EEG 55', 'EEG VREF'],
        'T013_D002_V00_2017_05_16_Emily-Focus-30Hzfilt.edf': ['STI 014', 'EEG 55', 'EEG VREF'],
        'T013_D003_V00_2017_05_16_Giulio-Resting-State-30Hzfilt.edf': ['STI 014', 'EEG 10', 'EEG 63', 'EEG VREF'],
        'T013_D004_V00_2017_05_16_Giulio-Focused-30Hzfilt.edf': ['STI 014', 'EEG 10', 'EEG 63', 'EEG VREF'],
        'T013_D005_V00_2017_05_15_Patrick-Resting-State-30Hzfilt.edf': ['STI 014', 'EEG 10', 'EEG 63', 'EEG VREF'],
        'T013_D006_V00_2017_05_15_Patrick-Focus-30Hzfilt.edf': ['STI 014', 'EEG 10', 'EEG 63', 'EEG VREF'],
        'T013_D007_V00_2017_05_16_MichaelH-Resting-State-30Hzfilt.edf': ['STI 014', 'EEG 10', 'EEG 63', 'EEG VREF'],
        'T013_D008_V00_2017_05_16_MichaelH-Focus-30Hzfilt.edf': ['STI 014', 'EEG 10', 'EEG 63', 'EEG VREF'],
        'T013_D009_V00_2017_05_15_Yana-Resting-State-30Hzfilt.edf': ['STI 014', 'EEG 18', 'EEG 23', 'EEG 46', 'EEG 56', 'EEG VREF'],
        'T013_D010_V00_2017_05_15_Yana-Focus-30Hzfilt.edf': ['STI 014', 'EEG 18', 'EEG 56', 'EEG VREF'],
    }, nThreads=8)
    # """
    # viz.showEdfSignal('data/T013_D006_V00_2017_05_15_Patrick-Focus-30Hzfilt.edf') # Use this to pick bad channels above.
