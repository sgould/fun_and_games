#!/usr/bin/env python
#
# Script to convert a continuous time video into a stop motion video.
#

import cv2
import os

import tkinter as tk
from tkinter import filedialog

app_wnd = tk.Tk()
app_wnd.withdraw() # hide application window
FILE_IN = tk.filedialog.askopenfilename(title="Open Video", filetypes=(("Video Files", ("*.mp4", "*.avi")), ("All Files", "*.*")))
if not FILE_IN: exit(0)


FILE_OUT = os.path.join(os.path.dirname(FILE_IN), os.path.splitext(os.path.basename(FILE_IN))[0] + "_motion.mp4")

print("reading from {}".format(FILE_IN))
print("writing to {}".format(FILE_OUT))

SKIPFRAMES = 30*5  # skip duration in number of frames

cap = cv2.VideoCapture(FILE_IN)
if not cap.isOpened(): exit(0)

fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
#fourcc = cv2.VideoWriter_fourcc(*'h264')
writer = None

count = 0
width, height = None, None
while (cap.isOpened()):
    ret, frame = cap.read()
    if ret:
        #if count % SKIPFRAMES == 0:
        height, width = frame.shape[0:2]
        if writer is None:
            writer = cv2.VideoWriter(FILE_OUT, fourcc, 30, (width, height))
        writer.write(frame)
        print("\r...{} ({}-by-{})".format(count, width, height), end="")

        count += SKIPFRAMES
        cap.set(cv2.CAP_PROP_POS_FRAMES, count)
    else:
        break

writer and writer.release()

print("\nwrote {} frames of size {}-by-{}".format(int((count + SKIPFRAMES - 1) / SKIPFRAMES), width, height))
print("done")