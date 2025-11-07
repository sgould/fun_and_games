# REDUCTION MAPPINGS
# Stephen Gould <stephen.gould@anu.edu.au>
#

import numpy as np
import matplotlib.pyplot as plt
import cv2

from matplotlib import cm
plt.rcParams.update({'font.size': 16})

#def psi(x): return np.zeros_like(x)
#def psi(x): return x
def psi(x): return x + 2.0 * np.sin(x)

bIsolated = True
bPlotReducedFcn = False
bVidAnimation = True
VID_FILENAME = "reduction_mapping_ani.mp4"

if bIsolated:
    def f(x, y): return x ** 2 + 2.0 * (y - x) ** 2

    x = np.arange(-5, 5, 0.25)
    y = np.arange(-5, 5, 0.25)
else:
    def f(x, y):
        z_1 = np.where(np.abs(x) < 1.0, 0.0, np.power(np.abs(x) - 1.0, 4.0))
        z_2 = (y - np.sin(x)) ** 2
        return z_1 + z_2

    x = np.arange(-4, 4, 0.25)
    y = np.arange(-4, 4, 0.25)

X, Y = np.meshgrid(x, y)

if bPlotReducedFcn:
    fig = plt.figure(figsize=(8, 6), dpi=75)
    plt.plot(x, f(x, 0 * x), 'k--')
    plt.plot(x, f(x, x), 'k-')
    plt.plot(x, f(x, x + 2.0 * np.sin(x)), 'k:')
    plt.legend([r"$x_2 = 0$", r"$x_2 = x_1$", r"$x_2 = x_1 + 2 \sin x_1$"])
    plt.gca().set_xlabel('$x_1$')
    plt.gca().set_ylabel(r'$F(x_1) = f(x_1, \Psi(x_1))$')

    plt.show()
    exit(0)


def draw_frame(azim=-75, fig=None):
    """Draws a video frame with given viewing angle."""

    if fig is None:
        fig = plt.figure(figsize=(16, 9), dpi=150 if bVidAnimation else 75)
        fig.tight_layout(pad=0)
    else:
        fig.clear()

    # plot the surface
    ax = fig.add_subplot(1, 2, 1, projection='3d')
    ax.plot_surface(X, Y, f(X, Y), cmap=cm.coolwarm, linewidth=0, antialiased=False, alpha=0.5)
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_zticklabels([])
    ax.set_xlabel('$x_1$')
    ax.set_ylabel('$x_2$')
    ax.set_title(r'$f(x_1, x_2)$')

    # plot the reduction mapping
    ax.plot(x, psi(x), f(x, psi(x)), color='black', ls='-', lw=2)

    # set the view (default: 30, -60, 0)
    ax.view_init(elev=30, azim=azim, roll=0)

    # plot the projection
    ax = fig.add_subplot(2, 2, 2)
    ax.contour(X, Y, f(X, Y), cmap=cm.coolwarm)
    ax.plot(x, psi(x), color='black', ls='--', lw=2)
    if bIsolated:
        ax.plot(0, 0, marker='o', color='black')
        plt.text(0.25, -0.25, r'$(x_1^\star, x_2^\star)$', color='black')
    else:
        sx = np.linspace(-1.0, 1.0)
        sy = np.sin(sx)
        ax.plot(sx, sy, color='black', lw=4)
        plt.text(1.25, 0.75, r'$(x_1^\star, x_2^\star)$', color='black')

    ax.axis('square')
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_xlabel('$x_1$')
    ax.set_ylabel(r'$x_2 = \Psi(x_1)$')

    # plot the reduced function
    ax = fig.add_subplot(2, 2, 4)
    ax.plot(x, f(x, psi(x)), color='black', ls='-', lw=2)
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_xlabel('$x_1$')
    ax.set_ylabel(r'$F(x_1) = f(x_1, \Psi(x_1))$')

    return fig

# render video or just show the image
if bVidAnimation:
    video, fig = None, None
    for theta in range(-75, 360-75, 1):
        fig = draw_frame(azim=theta, fig=fig)
        fig.canvas.draw()
        img = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8)
        img = img.reshape(fig.canvas.get_width_height()[::-1] + (4,))

        # write video frame
        if video is None:
            width, height, _ = img.shape
            fourcc = cv2.VideoWriter_fourcc(*'h264')
            video = cv2.VideoWriter(VID_FILENAME, fourcc, 30, (height, width))

        img = cv2.cvtColor(img[:, :, 1:4], cv2.COLOR_RGB2BGR)
        video.write(img)

    if video:
        video.release()

else:
    draw_frame()

plt.show()

