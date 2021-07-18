#!/usr/bin/env python
#
# Script to make an animated gif from a directory of images.
#

import os

import tkinter as tk
from tkinter import messagebox, filedialog
import cv2, imageio

IMG_SIZE = (480, 640)
# TODO: have crop set by showing first image and selecting region
IMG_CROP = (980, 60, 3100 - 980, 2875 - 60)

app_wnd = tk.Tk()
app_wnd.withdraw() # hide application window
IMG_LIST = tk.filedialog.askopenfilename(parent=app_wnd, title="Select Images", multiple=True,
    filetypes=(("JPEG Files", "*.jpg"), ("PNG Files", "*.png"), ("All Files", "*.*")))
if not IMG_LIST: exit(0)

GIF_FILE = tk.filedialog.asksaveasfilename(parent=app_wnd, title="Output File", filetypes=(("GIFs", "*.gif"), ("All Files", "*.*")))
if not GIF_FILE: exit(0)

images = []
for img_file in IMG_LIST:
    print("Processing {}...".format(img_file))
    img = imageio.imread(img_file)
    if IMG_CROP is not None:
        x, y, w, h = IMG_CROP
        img = img[y:y+h, x:x+w]
    if IMG_SIZE is not None:
        img = cv2.resize(img, IMG_SIZE)
    images.append(img)

print("Writing to {}...".format(GIF_FILE))
imageio.mimsave(GIF_FILE, images, duration=0.1)
print("...done")