#!/usr/bin/env python
#
# Script to merge two or more videos.
#

import cv2
import os

import tkinter as tk
from tkinter import filedialog

FILES_IN = []
app_wnd = tk.Tk()
app_wnd.withdraw() # hide application window
while True:
    file = tk.filedialog.askopenfilename(title="Open Video #{}".format(len(FILES_IN) + 1), filetypes=(("Video Files", ("*.mp4", "*.avi")), ("All Files", "*.*")))
    if not file: break
    FILES_IN.append(file)

if len(FILES_IN) < 2: exit(0)

FILE_OUT = os.path.join(os.path.dirname(FILES_IN[0]), os.path.splitext(os.path.basename(FILES_IN[0]))[0] + "_merged.mp4")

print("reading from \n...{}".format("\n...".join(FILES_IN)))
print("writing to {}".format(FILE_OUT))

writer = None
width, height = None, None

for file in FILES_IN:
    cap = cv2.VideoCapture(file)
    if not cap.isOpened():
        print("WARNING: could not open {}".format(file))
        continue

    while (cap.isOpened()):
        ret, frame = cap.read()
        if ret:
            height, width = frame.shape[0:2]
            if writer is None:
                fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
                writer = cv2.VideoWriter(FILE_OUT, fourcc, 30, (width, height))
            writer.write(frame)
        else:
            break

writer and writer.release()
