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

SECONDS_PER_CHUNK = 60 # seconds in each analysis window
SECONDS_PER_STEP  = 10 # offset between window starts.
BORDER_OFFSET_SEC = 60 # Seconds dropped at the start/end of each recording.

# Which frequency bands we want to calculate average power for.
BAND_FREQUENCIES = {
    'theta': [3.5, 7.5],
    'beta': [13.0, 30.0],
}


def bandPower(raw, fMin, fMax):
    """
    Given raw signal, and frequency bounds, chops the signal into windows and returns the
    average power within those bands for each window.
    """
    # Convert seconds to samples:
    sampleRate = int(raw.info['sfreq'])
    samplesPerChunk = SECONDS_PER_CHUNK * sampleRate
    samplesPerStep  = SECONDS_PER_STEP  * sampleRate
    startSample     = BORDER_OFFSET_SEC * sampleRate
    endSample       = raw._data.shape[1] - BORDER_OFFSET_SEC * sampleRate

    # which channels we are using...
    pickIDs = None if PICKS is None else mne.pick_types(raw.info, eeg=True, selection=PICKS)

    powers = []
    for at in range(startSample, endSample, samplesPerStep):
        # Uncomment to get progress updates:
        # print "%0.02f %%" % (100 * (at - startSample) * 1.0 / (endSample - startSample))
        # convert samples back to time:
        tMin, tMax = at * 1.0 / sampleRate, (at + samplesPerChunk) * 1.0 / sampleRate
        psds, freqs = mne.time_frequency.psd_multitaper(raw, fmin=fMin, fmax=fMax, tmin=tMin, tmax=tMax, picks=pickIDs)
        # Note: just averaged, so needs to be scaled if integral is desired.
        powers.append(np.mean(psds))
    return np.array(powers)


def bandStrength(pathAndBads):
    """
    Given an array [path, badChannels], load the data and return power data for each channel
    """
    path, bads = pathAndBads[0], pathAndBads[1]
    raw = mne.io.read_raw_edf("data/" + path, preload=True)
    raw.info['bads'] = bads

    result = {'path': path}
    for bandID, bandHz in BAND_FREQUENCIES.iteritems():
        # TODO: calculate all in a single call, by splitting up one psd result.
        result[bandID] = bandPower(raw, bandHz[0], bandHz[1])
    return result


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
    ax[0, 1].set_title('theta/beta')
    ax[1, 1].set_title('legend')

    for i, result in enumerate(results):
        dot = '-' if i % 2 == 0 else '--' # line for Focus, dash for rest
        col = [(1,0,0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, 0, 1), (0, 1, 1)][i // 2] # One colour per person
        t, b = result['theta'], result['beta']
        ax[0, 0].plot(t, c=col, ls=dot)
        ax[1, 0].plot(b, c=col, ls=dot)
        ax[0, 1].plot(t / b, c=col, ls=dot)
        # Fourth plot just for legend
        ax[1, 1].plot(t[0], c=col, ls=dot, label=result['path'])

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
    # viz.showEdfSignal('Pat-Rest.edf') # Use this to pick bad channels above.
