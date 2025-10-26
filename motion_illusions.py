#!/usr/bin/env python
#
# MOTION ILLUSIONS
# Creates some classic optical illusions involving perceived motion.
#

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle
from matplotlib.colors import hsv_to_rgb
import imageio


def shade_face(ax, origin, n=256, angle=0.0, outer_radius=1.0, inner_radius=0.5):
    """Shade the face of an annulus and add it to the given axis."""

    for i in range(n):
        colour = hsv_to_rgb((i/n, 1.0, 1.0))
        theta1 = 360*i/n + angle
        theta2 = 360 * (i + 1) / n + angle
        wedge = Wedge(center=origin, r=outer_radius, theta1=theta1, theta2=theta2, facecolor=colour, edgecolor=colour, linewidth=1)
        ax.add_patch(wedge)
    #ax.add_patch(Circle(origin, outer_radius, facecolor=None, edgecolor='black', linewidth=0, fill=False))
    ax.add_patch(Circle(origin, inner_radius, facecolor='lightgray', edgecolor='black', linewidth=0))

    return ax


def shade_edge(ax, origin, n=256, angle=0.0, outer_radius=1.0, inner_radius=0.5, steps=4):
    """Shade the edge of an annulus and add it to the given axis."""

    t = np.linspace(0.0, 1.0, n) + angle / 360.0
    x = np.cos(2.0 * np.pi * t)
    y = np.sin(2.0 * np.pi * t)

    for i in range(n-1):
        colour = hsv_to_rgb((0.5, 1.0, ((i * steps % n) / n)))
        ax.plot(outer_radius * x[i:i+2] + origin[0], outer_radius * y[i:i+2] + origin[1], color=colour, lw=0.5, alpha=0.5)
        ax.plot(inner_radius * x[i:i+2] + origin[0], inner_radius * y[i:i+2] + origin[1], color=colour, lw=0.5, alpha=0.5)

    return ax


frames = []

for counter, angle in enumerate(range(0, 360, 15)):
    print("generating frame {}".format(angle))

    f = plt.figure()
    f.tight_layout(pad=0)
    f.patch.set_facecolor('lightgray')

    ax = f.gca()
    ax.set_position([0, 0, 1, 1])
    ax.set_xlim((-1.05, 3.3))
    ax.set_ylim((-2.125, 2.125))
    ax.axis('square')
    ax.set_axis_off()

    shade_face(ax, (0, 0), 256, angle=angle)
    shade_face(ax, (2.25, 0), 256, angle=angle)

    shade_edge(ax, (0, 0), 256, angle=0 if counter % 2 == 0 else 45)
    shade_edge(ax, (2.25, 0), 256, angle=45 if counter % 2 == 0 else 0)

    # grab figure as an image
    f.canvas.draw()
    img = np.frombuffer(f.canvas.tostring_rgb(), dtype=np.uint8)
    img = img.reshape(f.canvas.get_width_height()[::-1] + (3,))
    plt.close(f)

    frames.append(img)


filename = "motion.gif"
print("writing animated GIF to {} ...".format(filename))
imageio.mimsave(filename, frames, duration=1/30)
