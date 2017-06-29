"""
Performs analysis on the synchronization output of waveletGenerator.py
"""

import matplotlib.pyplot as plt
import mne
import numpy as np

import viz

# Channels to include in the analysis:
#           F3       FpZ       Fz      Fp2       F4        F8
PICKS = ['EEG 12', 'EEG 8', 'EEG 6', 'EEG 5', 'EEG 60', 'EEG 58']
PICK_FMT = ['F3',   'FpZ',    'Fz',   'Fp2',    'F4',     'F8'  ]
# ignored: 'EEG 10', Fp1 (Many missing)
# ignored: 'EEG 18', F7  (Yana Missing)


# Find the indexes of 'want' within the list 'have'
def findIndexes(have, want):
    haveList = have.tolist()
    result = np.zeros(len(want), dtype='int')
    for i in range(len(want)):
        result[i] = haveList.index(want[i])
    return result

# Process a single trial's synchronization
def analyzeOne(path, bads, person, type):
    print("Processing %s, %s" % (person, type))

    # 1) Load edf to get channel names, convert to index
    raw = mne.io.read_raw_edf("data/" + path, preload=True, verbose=False)
    raw.info['bads'] = bads
    processedChannels = mne.pick_types(raw.info, eeg=True, selection=None)
    wantedChannels = mne.pick_types(raw.info, eeg=True, selection=PICKS)
    indexes = findIndexes(processedChannels, wantedChannels)

    # 2) Load synchronization data
    Q = 100 # Whatever was used by waveletGenerator
    syncFile = "output/synchro/%s-%s_q=%d.csv" % (person, type, Q)
    syncData = np.genfromtxt(syncFile, delimiter=', ')
    syncData = syncData[indexes[:, None], indexes]
    return syncData

# Analyze all trials, given EEG path and bad channels
def analyzeAll(badMapping):
    results = {}

    allMin, allMax = None, None
    for path, bads in badMapping.iteritems():
        shortName = viz.shortName(path)
        [person, type] = shortName.split('-')
        if person not in results:
            results[person] = {}
        # Perform the analysis
        result = analyzeOne(path, bads, person, type)

        # Normalize the name of the type
        normType = type
        if normType == 'Focused':
            normType = 'Focus'
        results[person][normType] = result

        # And keep track of the global synchronization range
        if allMin is None:
            allMin, allMax = np.min(result), np.max(result)
        else:
            allMin = min(allMin, np.min(result))
            allMax = max(allMax, np.max(result))
    return results, allMin, allMax

# Display all results, for each person, state, and difference between states.
def displayResults(results, allMin, allMax):
    PEOPLE = ['Emily', 'Giulio', 'Patrick', 'MichaelH', 'Yana']
    TYPES = ['Focus', 'Resting']

    # Plot the actual synchronization matrix data as color plots
    ax = viz.cleanSubplots(len(TYPES) + 1, len(PEOPLE), pad=0.05, axes=False)
    for i in range(len(TYPES)):
        for j in range(len(PEOPLE)):
            ax[i][j].pcolor(results[PEOPLE[j]][TYPES[i]], vmin=allMin, vmax=allMax)
    for j in range(len(PEOPLE)):
        ax[len(TYPES)][j].pcolor(
            results[PEOPLE[j]][TYPES[0]] - results[PEOPLE[j]][TYPES[1]],
            vmin=allMin - allMax, vmax=allMax - allMin)

    # Y axes formatting on the left.
    for i in range(len(TYPES)):
        ax[i][0].set_ylabel(TYPES[i])
        ax[i][0].set_yticks(np.arange(len(PICKS)) + 0.5)
        ax[i][0].set_yticklabels(PICK_FMT)
    ax[len(TYPES)][0].set_ylabel("%s - %s" % (TYPES[0], TYPES[1]))
    ax[len(TYPES)][0].set_yticks(np.arange(len(PICKS)) + 0.5)
    ax[len(TYPES)][0].set_yticklabels(PICKS)

    # X axis formatting on top/bottom:
    for j in range(len(PEOPLE)):
        ax[0][j].set_title(PEOPLE[j])
        ax[len(TYPES)][j].set_xticks(np.arange(len(PICKS)) + 0.5)
        ax[len(TYPES)][j].set_xticklabels(PICK_FMT)

    plt.show()



if __name__ == '__main__':
    results, allMin, allMax = analyzeAll({
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
    })
    displayResults(results, allMin, allMax)
