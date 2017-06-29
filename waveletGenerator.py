"""
Code that performs wavelet synchronization analysis of a single EEG trial.
Given an edf input, and a set of bad channels,
 this calculates synchronization against all other channel pairs,
 and writes the output to output/synchro/$file
"""

import matplotlib.pyplot as plt
import mne.io
import numpy as np
from tqdm import tqdm

import collections
import functools

import viz

class memoized(object):
    '''Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    '''
    def __init__(self, func):
        self.func = func
        self.cache = {}
    def __call__(self, *args):
        if not isinstance(args, collections.Hashable):
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return self.func(*args)
        if args in self.cache:
            return self.cache[args]
        else:
            value = self.func(*args)
            self.cache[args] = value
            return value
    def __repr__(self):
        '''Return the function's docstring.'''
        return self.func.__doc__
    def __get__(self, obj, objtype):
        '''Support instance methods.'''
        return functools.partial(self.__call__, obj)

START_TIME_SEC = 1
END_TIME_SEC = 4.5 * 60

# Dimension of points to use (i.e. sliding window size)
PARAM_d = 10
# Skip length in taking the last PARAM_d points
PARAM_T = 1
# Probability cutoff
P_REF = 0.05
# Windows closer to reference than this are ignored
W1 = (PARAM_d - 1) * PARAM_T
# Windows further to reference than this are ignored. Set later.
W2 = None

# Downsampling for when calculating the average synchronicity
Q = 100
print("\n***Debug: Wrong Q! Should be set to 4\n")

# Channels to include in the analysis:
#          Fp1        F3        F7       FpZ       Fz      Fp2       F4        F8
# PICKS = ['EEG 10', 'EEG 12', 'EEG 18', 'EEG 8', 'EEG 6', 'EEG 5', 'EEG 60', 'EEG 58']
PICKS = None # all non-bad channels.
# Although EEG 8 is technically AFz, but is the closest to FpZ

# Global signal, (k channels x n samples)
SIGNAL = None


# Euclidean distance between two vectors
def dist(X1, X2):
    return np.linalg.norm(X1 - X2)

# X vector from paper
# @memoize
def X(k, n):
    return SIGNAL[k, n : n + PARAM_d * PARAM_T : PARAM_T]

# Probability that dist(X_k,m, X_k,n) < ekn for given X_k,n
# @memoize
def PeknKN(ekn, k, n):
    closeCount = 0
    Xkn = X(k, n)
    for m in range(n - W1, n - W2, -1):
        if dist(X(k, m), Xkn) < ekn:
            closeCount += 1
    for m in range(n + W1, n + W2):
        if dist(X(k, m), Xkn) < ekn:
            closeCount += 1
    return (1. / (2. * (W2 - W1))) * closeCount

# Return the largest E_k,n such that P(dist(X_k,m, X_k,n) < ekn) < P_REF
@memoized
def E(k, n):
    delta = 1e-6
    ekn = 0
    while PeknKN(ekn, k, n) < P_REF:
        ekn += delta
    return ekn - delta

# Hn,m = # channels where dist(X_k,m, X_k,n) < ekn for that channel
@memoized
def H(n, m):
    closeCount = 0
    for k in range(SIGNAL.shape[0]):
        if dist(X(k, n), X(k, m)) < E(k, n):
            closeCount += 1
    return closeCount

# Skn = Syncrhonization likelihood for each channel
@memoized
def S(k, n):
    M = SIGNAL.shape[0]
    Xkn, Ekn = X(k, n), E(k, n)

    closeWeight = 0.
    for m in range(n - W1, n - W2, -1):
        if dist(X(k, m), Xkn) < Ekn:
            closeWeight += (H(n, m) - 1.) / (M - 1.)
    for m in range(n + W1, n + W2):
        if dist(X(k, m), Xkn) < Ekn:
            closeWeight += (H(n, m) - 1.) / (M - 1.)
    return (1. / (2. * P_REF * (W2 - W1))) * closeWeight

# SLk = Average Syncrhonization likelihood for channel k
@memoized
def SL(k):
    n0 = W2
    N = len(SIGNAL[k])
    allSL = []
    for n in tqdm(range(n0, N - W2 - 1, Q)):
        allSL.append(S(k, n))
    return np.mean(allSL)

# BS_k,r,n = Bivariate Synchronicity between channels k & r, at time n
@memoized
def BS(k, r, n):
    M = SIGNAL.shape[0]
    Xkn, Ekn = X(k, n), E(k, n)
    Xrn, Ern = X(r, n), E(r, n)

    closePairCount = 0.
    for m in range(n - W1, n - W2, -1):
        if dist(X(k, m), Xkn) < Ekn and dist(X(r, m), Xrn) < Ern:
            closePairCount += 1
    for m in range(n + W1, n + W2):
        if dist(X(k, m), Xkn) < Ekn and dist(X(r, m), Xrn) < Ern:
            closePairCount += 1
    return (1. / (2. * P_REF * (W2 - W1))) * closePairCount

# BS_k,r = Average Bivariate Synchronicity between channels k & r
@memoized
def BSL(k, r):
    n0 = W2
    N = len(SIGNAL[k])
    allSL = []
    for n in tqdm(range(n0, N - W2 - 1, Q)):
        allSL.append(BS(k, r, n))
    return np.mean(allSL)

# Show Ekns for all n for a given channel k
def plotEkns(k):
    N = SIGNAL.shape[1]
    ekns = []
    for nAt in range(W2, N - W2 - 1, 100):
        c = N - 2 * W2 - 1
        p = int(c // 20)
        if (nAt - W2) % p == 0:
            print("%d%%" % (5 * (nAt - W2) / p))
        ekns.append(E(k, nAt))
    plt.plot(ekns)
    plt.show()

# Show Skns for all n for a given channel k
def plotSkns(k):
    N = SIGNAL.shape[1]
    ekns = []
    for nAt in range(W2, N - W2 - 1, 20):
        c = N - 2 * W2 - 1
        p = int(c // 20)
        if (nAt - W2) % p == 0:
            print("%d%%" % (5 * (nAt - W2) / p))
        ekns.append(S(k, nAt))
    plt.plot(ekns)
    plt.show()

# Show SLks for all k:
def plotSLks():
    M = SIGNAL.shape[0]
    slks = []
    for k in range(M):
        print("Calculating %d / %d" % (k+1, M))
        slks.append(SL(k))
    plt.plot(slks)
    plt.show()

# Pairwise covariance matrix of Bivariate Synchronicity for all channels:
def plotBSLs(longName):
    M = SIGNAL.shape[0]
    bsls = np.zeros((M, M))

    allK, allR = np.meshgrid(range(M), range(M))
    allK, allR = allK.ravel(), allR.ravel()
    for k, r in zip(tqdm(allK), allR):
        bsls[k, r] = BSL(k, r)
    print(bsls)

    shortName = viz.shortName(longName)
    outputFile = "output/synchro/%s_q=%d.csv" % (shortName, Q)
    print("Saving to %s..." % outputFile)
    np.savetxt(outputFile, bsls, delimiter=', ', fmt='%.8f')

    viz.correlationMatrix(bsls)


# Still in progress...don't run yet...
def process(signal, sRate, longName):
    global SIGNAL, W2
    SIGNAL = signal
    W2 = int(sRate // 2)
    plotBSLs(longName)



def main():
    # path = 'T013_D001_V00_2017_05_16_Emily-Resting-30Hzfilt.edf'
    path = 'T013_D010_V00_2017_05_15_Yana-Focus-30Hzfilt.edf'
    bads = ['STI 014', 'EEG 18', 'EEG 56', 'EEG VREF']
    raw = mne.io.read_raw_edf("data/" + path, preload=True)
    raw = raw.crop(tmin=START_TIME_SEC, tmax=END_TIME_SEC)
    raw.info['bads'] = bads

    pickIDs = mne.pick_types(raw.info, eeg=True, selection=PICKS)
    data = np.take(raw._data, pickIDs, axis=0)
    print(data.shape)

    sRate = raw.info['sfreq']
    process(data, sRate, path)



if __name__ == '__main__': main()
