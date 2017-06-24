"""
Note: STILL IN PROGRESS!
"""

import matplotlib.pyplot as plt
import mne.io
import numpy as np

START_TIME_SEC = 1
END_TIME_SEC = 4.5 * 60

# Dimension of points to use (i.e. sliding window size)
PARAM_d = 10
# Skip length in taking the last PARAM_d points
PARAM_T = 1
# Probability cutoff
P_REF = 0.05

#          Fp1        F3
PICKS = ['EEG 10', 'EEG 12']

# Euclidean distance between two vectors
def dist(X1, X2):
    return np.linalg.norm(X1 - X2)

# X vector from paper
def getX(signal, n):
    return signal[n:n + PARAM_d * PARAM_T:PARAM_T]

# Scaled P value for a given channel and ekn
def PeknKN(signal, w1, w2, ekn, n):
    scale = 1. / (2. * (w2 - w1))
    closeCount = 0
    Xkn = getX(signal, n)
    for i in range(n - w1, n - w2, -1):
        if dist(getX(signal, i), Xkn) < ekn:
            closeCount += 1
    for i in range(n + w1, n + w2):
        if dist(getX(signal, i), Xkn) < ekn:
            closeCount += 1
    return scale * closeCount

# Find e_k,n error threshold given channel and window sizes
def pickEkn(signal, n, w1, w2):
    bestEkn = 0
    ekn = 0
    while PeknKN(signal, w1, w2, ekn, w2) < P_REF:
        ekn += 1e-6
    return ekn

# H_n,m from the paper
def calcHNM(allSignals, allEKNs, n, m, d, T):
    M = allSignals.shape[0]
    closeCount = 0
    for k in range(M):
        signal = allSignals[k,:]
        ekns = allEKNs[k,:]
        if dist(getX(signal, n), getX(signal, m)) < ekns[n]:
            closeCount += 1

# S_k,n from the paper
def calcSKN(allSignals, allEKNs, k, n, w1, w2):
    M = allSignals.shape[0]
    signal = allSignals[k,:]
    scale = 1. / (2. * P_REF * (w2 - w1))
    Xkn = getX(signal, n)
    closeWeight = 0.
    for i in range(n - w1, n - w2, -1):
        if dist(getX(signal, i), Xkn) < allEKNs[k,n]:
            closeWeight += (HNM[n,m] - 1.) / (M - 1.)
    for i in range(n + w1, n + w2):
        if dist(getX(signal, i), Xkn) < ekn:
            closeWeight += (HNM[n,m] - 1.) / (M - 1.)
    return scale * closeWeight

# SL_k from the paper
def calcSLk(allSignals, allEKNs, k):
    N = allSignals.shape[1]
    n0 = 1
    q = 4
    allSL = []
    for n in range(n0, N, q):
        allSL.append(calcSKN(allSignals, allEKNs, k, n, w1, w2))
    return np.mean(allSL)

# Still in progress...don't run yet...
def process(signal, sRate):
    d = 10
    T = 1
    w1 = (PARAM_d - 1) * PARAM_T
    w2 = int(sRate // 2)

    ekns = []
    for nAt in range(w2, len(signal) - w2, 100):
        c = len(signal) - 2 * w2
        p = int(c // 20)
        if (nAt - w2) % p == 0:
            print "%d%%" % (5 * (nAt - w2) / p)
        ekns.append(pickEkn(signal, nAt, w1, w2))

    plt.plot(ekns)
    plt.show()

def main():
    path = 'T013_D001_V00_2017_05_16_Emily-Resting-30Hzfilt.edf'
    bads = ['STI 014', 'EEG 55', 'EEG VREF']
    raw = mne.io.read_raw_edf("data/" + path, preload=True)
    raw = raw.crop(tmin=START_TIME_SEC, tmax=END_TIME_SEC)
    raw.info['bads'] = bads

    pickIDs = mne.pick_types(raw.info, eeg=True, selection=PICKS)
    data = np.take(raw._data, pickIDs, axis=0)
    print data.shape

    sRate = raw.info['sfreq']
    process(data[0, :], sRate)


if __name__ == '__main__': main()
