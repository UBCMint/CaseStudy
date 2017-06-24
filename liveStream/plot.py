import argparse
import math
import matplotlib.pyplot as plt
import numpy as np

# pip3 install python-osc
from pythonosc import dispatcher
from pythonosc import osc_server
# See here for example:
# http://developer.choosemuse.com/research-tools-example/grabbing-data-from-museio-a-few-simple-examples-of-muse-osc-servers#python

import livegraph
import livehist

# Utility to make all the subplots we need.
def cleanSubplots(r=2, c=4, pad=0.05):
    f = plt.figure()
    f.subplots_adjust(left=pad, right=1.0-pad, top=1.0-pad, bottom=pad, hspace=pad*4)
    axes, at = [], 1
    for i in range(r):
        row = []
        for j in range(c):
            row.append(f.add_subplot(r, c, at))
            at = at + 1
        axes.append(row)
    return axes

plots = []
lastG = None
lastB = None
lastT = None

# Process the latest batch of isGood, theta, beta for each channel.
def process(g, t, b):
    for i in range(4):
        r = i // 2
        for c in range(2 * (i % 2), 2 * (i % 2 + 1)): # two graphs per channel
            plots[r][c].setGood(g[i] == 1)
            plots[r][c].add(np.log(t[i]/b[i])) # Use log ratio for now
    plt.pause(0.001)

# Process the status only once all the values are available
def tryProcess():
    global lastG, lastB, lastT
    if lastG is None or lastB is None or lastT is None:
        return
    process(lastG, lastB, lastT)
    lastG, lastB, lastT = None, None, None # Clear status, ready for next ones.

# isGood returned, process if it's the last to show up
def gHandler(unused_addr, ch1, ch2, ch3, ch4):
    global lastG
    lastG = [ch1, ch2, ch3, ch4]
    tryProcess()

# relative beta returned, process if it's the last to show up
def bHandler(unused_addr, ch1, ch2, ch3, ch4):
    global lastB
    lastB = [ch1, ch2, ch3, ch4]
    tryProcess()

# relative theta, process if it's the last to show up
def tHandler(unused_addr, ch1, ch2, ch3, ch4):
    global lastT
    lastT = [ch1, ch2, ch3, ch4]
    tryProcess()

# Convert channel id (0-3) to name.
def getTitle(channel):
    return [
        'TP9 (left ear)',
        'Fp1 (left front)',
        'Fp2 (right front)',
        'TP10 (right ear)',
    ][channel]

if __name__ == "__main__":
    # Note: Serve Muse by running:
    #   ./muse-io --osc osc.udp://localhost:5000 --device <device ID>
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        default="127.0.0.1",
                        help="The ip to listen on")
    parser.add_argument("--port",
                        type=int,
                        default=5000,
                        help="The port to listen on")
    args = parser.parse_args()

    # Listen to OSC channels we care about:
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/debug", print)
    dispatcher.map("/muse/elements/is_good", gHandler)
    dispatcher.map("/muse/elements/beta_relative", bHandler)
    dispatcher.map("/muse/elements/theta_relative", tHandler)

    # Build live graphs
    axes = cleanSubplots()
    for i in range(len(axes)):
        plotRow = []
        for j in range(len(axes[i])):
            title = getTitle(i * 2 + j // 2)
            if j % 2 == 0:
                plotRow.append(livegraph.LiveGraph(axes[i][j], title))
            else:
                plotRow.append(livehist.LiveHist(axes[i][j], title))
        plots.append(plotRow)

    # server = osc_server.ThreadingOSCUDPServer(
    server = osc_server.BlockingOSCUDPServer(
        (args.ip, args.port), dispatcher)
    print("Serving on {}".format(server.server_address))
    server.serve_forever()
