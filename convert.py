"""
Bunch of file format conversion utilities.
"""

import csv
import mne.io

# Format floats as strings to 6sf. NOTE: maybe not needed?
def sixSF(readings):
    return [format(x, '.6f') for x in readings]

# Given an array of positions (x,y,z), noralize them all to length 1 vectors.
def normalPos(positions):
    fPos = np.array([[float(p) for p in pos] for pos in positions])
    return [row / numpy.linalg.norm(row) for row in fPos]


def edfToCSV(edfPath, csvPath):
    """
    Convert an EDF file to the CSV that openVibe can load as signal
    """
    print "Loading %s..." % edfPath
    raw = mne.io.read_raw_edf(edfPath, preload=True)

    readings = raw._data.T
    channelNames = raw.info['ch_names']
    sampleRate = raw.info['sfreq']
    secPerSample = 1.0 / sampleRate

    print "# Readings: %d" % readings.shape[0]
    print "# Channels: %d" % len(channelNames)
    print "Sample rate: %d hz" % sampleRate

    print "Writing to %s..." % csvPath
    with open(csvPath, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(['Time (s)'] + channelNames + ['Sampling Rate'])
        # First row has extra rate:
        writer.writerow([0.0] + sixSF(readings[0].tolist()) + [sampleRate])
        for r in range(1, readings.shape[0]):
            writer.writerow([r * secPerSample] + sixSF(readings[r].tolist()))
    print "Done!"


def locationsToTxt(inPath, outPath):
    """
    Convert the location data provided for the headset to openvibe sensor location file.
    """
    print "Loading %s..." % inPath

    rows = []
    with open(inPath, 'rb') as inFile:
        reader = csv.reader(inFile, delimiter='\t')
        rows = [row for row in reader][3:67]

    channelNames = [row[0].replace('E', 'EEG ') for row in rows]
    channelList = " ".join('"' + name + '"' for name in channelNames)
    header = '[\n\t[ %s ]\n\t[ "x" "y" "z" ]\n]\n' % channelList
    positions = normalPos([row[1:] for row in rows])

    print "Writing %s..." % outPath
    with open(outPath, 'w') as outFile:
        outFile.write(header)
        for pos in positions:
            row = "[\n\t[ %s %s %s ]\n]\n" % tuple(pos)
            outFile.write(row)
    print "Done!"
