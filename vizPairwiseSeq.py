#!/usr/bin/env python3
# -----------------------------------------------------------------------
# VIZPAIRWISESEQ
# Copyright 2015, Stephen Gould <stephen.gould@anu.edu.au>
# -----------------------------------------------------------------------
# Script to visualize an integer sequence based on the visualization of
# the decimal expansion of \pi by Martin Krzywinski and Cristian Vasile.
# -----------------------------------------------------------------------

import math
import matplotlib.pyplot as plt
import matplotlib.patches as pth
import random
import sys

# --- distance to arc centre --------------------------------------------

def distance_to_centres(x, y, r):
    """Calculates the distance to the mid-point of an chord on the unit
    circle and the distance to the centre of a circle of a circle of
    radius r with the same chord."""

    h1 = 0.5 * math.sqrt((x[0] + x[1]) ** 2 + (y[0] + y[1]) ** 2)
    h2 = 0.5 * math.sqrt(4.0 * r ** 2 - (x[0] - x[1]) ** 2 - (y[0] - y[1]) ** 2)
    return (h1, h2)

# generate digits of pi -------------------------------------------------

def pi_digits(x):
    """Generate x digits of pi. Source: https://stackoverflow.com/questions/9004789/1000-digits-of-pi-in-python."""
    k,a,b,a1,b1 = 2,4,1,12,4
    while x > 0:
        p,q,k = k * k, 2 * k + 1, k + 1
        a,b,a1,b1 = a1, b1, p*a + q*a1, p*b + q*b1
        d,d1 = a/b, a1/b1
        while d == d1 and x > 0:
            yield int(d)
            x -= 1
            a,a1 = 10*(a % b), 10*(a1 % b1)
            d,d1 = a/b, a1/b1

# --- visualization -----------------------------------------------------

def visualize_sequence(int_seq, block=True):
    """Visualize a sequence of integers"""

    seq_length = len(int_seq)
    min_value = min(int_seq)
    max_value = max(int_seq)
    val_range = max_value - min_value + 1

    # convert a sequence of numbers to a sequence in [0.0, 1.0]
    counts = [0.02 * seq_length for i in range(val_range)]
    counted_seq = []
    for n in int_seq:
        counted_seq.append((n - min_value, counts[n - min_value]))
        counts[n - min_value] += 1.0

    linear_seq = [(p[0] + p[1] / counts[p[0]]) / float(val_range) for p in counted_seq]

    # set up plots
    fig = plt.figure()
    ax = plt.axes()
    ax.set_axis_off()
    ax.set_ylim([-1, 1])
    ax.set_xlim([-1, 1])
    fig.set_facecolor('black')
    fig.add_axes(ax)

    cm = plt.get_cmap('Paired')
    radius = 1.1

    # plot arcs connecting consecutive elements
    last_point = linear_seq.pop()
    for next_point in linear_seq:

        theta_last = 2 * math.pi * last_point
        theta_next = 2 * math.pi * next_point
        x = [math.cos(theta_last), math.cos(theta_next)]
        y = [math.sin(theta_last), math.sin(theta_next)]

        d = distance_to_centres(x, y, radius)
        scale = 0.5 * d[1] / d[0] + 0.5
        x_centre = scale * (x[0] + x[1])
        y_centre = scale * (y[0] + y[1])

        theta_1 = math.degrees(math.atan2(y[0] - y_centre, x[0] - x_centre))
        theta_2 = math.degrees(math.atan2(y[1] - y_centre, x[1] - x_centre))

        if (math.fmod(theta_2 - theta_1 + 720.0, 360.0) > 180.0):
            theta_1, theta_2 = theta_2, theta_1

        colour = cm(last_point)
        ax.add_patch(pth.Arc((x_centre, y_centre), 2.0 * radius, 2.0 * radius,
            angle=0, theta1=theta_1, theta2=theta_2, color=colour, fill=False, linewidth=0.25))
        last_point = next_point

    plt.show(block=block)

# --- main --------------------------------------------------------------

if __name__ == "__main__":

    int_seq = []
    if (len(sys.argv) == 1):
        #print("Generating a random sequence of digits...")
        #int_seq = [random.randint(0, 9) for i in range(2500)]
        print("Generating digits of pi...")
        int_seq = list(pi_digits(2500))
        #print("Generating linear sequence...")
        #int_seq = [i % 10 for i in range(2500)]
    else:
        print("Reading sequence from {0}...".format(sys.argv[1]))
        fh = open(sys.argv[1])
        int_seq = [int(i) for i in fh.read().split()]
        fh.close()

    visualize_sequence(int_seq)
