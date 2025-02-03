# NACA AIRFOIL ANIMATION

import numpy as np
import matplotlib.pyplot as plt
import cv2

def contour(x, m, p, t):
    """Upper and lower contour and camber for NACA wing at locations x."""

    camber = np.where(x < p, m / (p ** 2) * (2*p*x - np.square(x)), m / ((1 - p)**2) * ((1 - 2*p) + 2*p*x - np.square(x)))
    thickness = 5.0 * t * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * np.power(x, 2) + 0.2843 * np.power(x, 3) - 0.1015 * np.power(x, 4))
    angle = np.where(x < p, np.arctan(2*m / p**2 * (p - x)), np.arctan(2*m / (1 - p)**2 * (p - x)))

    dx = thickness * np.sin(angle)
    dy = thickness * np.cos(angle)

    upper = np.stack((x - dx, camber + dy))
    lower = np.stack((x + dx, camber - dy))

    return upper, lower, camber


naca_init = np.array((0.02, 0.3, 0.12))
naca_final = np.array((0.04, 0.42, 0.12))

t = np.linspace(0.0, 1.0, 60, endpoint=True)
x = np.linspace(0.0, 1.0, 200, endpoint=True)

f = plt.figure()
f.tight_layout(pad=0)

# generate frames
print("generating frames...")
upper0, lower0, curve0 = contour(x, naca_init[0], naca_init[1], naca_init[2])

frames = []
for ti in t:
    naca = (1.0 - ti) * naca_init + ti * naca_final

    upper, lower, curve = contour(x, naca[0], naca[1], naca[2])

    plt.gca().clear()
    plt.plot(x, curve0, 'b--', alpha=0.2)
    plt.plot(upper0[0,:], upper0[1,:], 'b', alpha=0.2)
    plt.plot(lower0[0,:], lower0[1,:], 'b', alpha=0.2)

    plt.plot(x, curve, 'b--')
    plt.plot(upper[0,:], upper[1,:], 'b')
    plt.plot(lower[0,:], lower[1,:], 'b')
    plt.ylim(-0.6, 0.6)
    plt.xlim(-0.1, 1.1)
    plt.grid('on')
    plt.gca().margins(0)

    f.canvas.draw()
    img = np.frombuffer(f.canvas.tostring_rgb(), dtype=np.uint8)
    img = img.reshape(f.canvas.get_width_height()[::-1] + (3,))
    #img = img.transpose((1,0,2))
    frames.append(img)

plt.show()

# write video
print("writing video...")
width, height, _ = frames[0].shape
fourcc = cv2.VideoWriter_fourcc(*'h264')
writer = None
try:
    writer = cv2.VideoWriter("naca_animation.mp4", fourcc, 30, (height, width))
    for img in frames:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        writer.write(img)

finally:
    writer and writer.release()




