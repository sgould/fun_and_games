#!/usr/bin/env python
#
# MAKE A TEST VIDEO
# Script to create a test video.
#
# Stephen Gould <stephen.gould@anu.edu.au>
#

import cv2
import numpy as np

WIDTH, HEIGHT = 640, 480
FPS = 30
NUM_FRAMES = 5 * 60 * FPS
VID_OUT = "test.mp4"

center = (WIDTH // 2, HEIGHT // 2)
radius = 3 * np.min((WIDTH, HEIGHT)) / 8
theta  = np.linspace(-0.5 * np.pi, 1.5 * np.pi, int(60 * FPS))

fourcc = cv2.VideoWriter_fourcc(*'h264')
writer = None
try:
    writer = cv2.VideoWriter(VID_OUT, fourcc, FPS, (WIDTH, HEIGHT))
    for i in range(NUM_FRAMES):
        # create image with test pattern
        img = np.zeros((HEIGHT, WIDTH, 3), np.uint8)
        pt = (int(center[0] + radius * np.cos(theta[i % len(theta)])), int(center[1] + radius * np.sin(theta[i % len(theta)])))
        #cv2.ellipse(img, center, (int(radius), int(radius)), 0.0, startAngle=-90.0, endAngle=180 * theta[i % len(theta)] / np.pi,
        #            color=(0, 0, 255), thickness=7, lineType=cv2.LINE_AA)
        cv2.line(img, center, pt, (0, 0, 255), 3, cv2.LINE_AA)
        cv2.circle(img, center, int(radius), (127, 127, 127), 3, cv2.LINE_AA)

        # add timestamp
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = "{:0.3f}".format(1.0 * i / FPS)
        textsize = cv2.getTextSize(text, font, 1.0, 2)[0]
        textX = WIDTH - textsize[0]
        textY = HEIGHT - textsize[1]
        cv2.putText(img, text, (textX, textY), font, 1.0, (255, 255, 255), 2, cv2.LINE_AA)

        writer.write(img)

finally:
    writer and writer.release()

print("done")
