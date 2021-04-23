#!/usr/bin/env python
#
# Script to reverse a video file.
#

import cv2
import tempfile
import os

import tkinter as tk
from tkinter import filedialog

app_wnd = tk.Tk()
app_wnd.withdraw() # hide application window
FILE_IN = tk.filedialog.askopenfilename(title="Open Video", filetypes=(("Video Files", ("*.mp4", "*.avi")), ("All Files", "*.*")))
if not FILE_IN: exit(0)

print("reading from {}".format(FILE_IN))

cap = cv2.VideoCapture(FILE_IN)
if not cap.isOpened(): exit(0)

TMP_DIR = tempfile.mkdtemp()

print("writing frames to {}".format(TMP_DIR))

count = 0
width, height = None, None
while (cap.isOpened()):
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(os.path.join(TMP_DIR, "{:06d}.png".format(count)), frame)
        height, width = frame.shape[0:2]
        count += 1
    else:
        break

print("{} frames read of size {}-by-{}".format(count, width, height))

exit(0)

FILE_OUT = os.path.join(TMP_DIR, "rev.mp4")

fourcc = cv2.VideoWriter_fourcc(*'h264')
writer = None
try:
    writer = cv2.VideoWriter(FILE_OUT, fourcc, 30, (width, height))
    for i in range(count, 0, -1):
        frame = cv2.imread(os.path.join(TMP_DIR, "{:06d}.png".format(i - 1)))
        writer.write(frame)

finally:
    writer and writer.release()

print("done")