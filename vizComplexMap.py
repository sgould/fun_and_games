#!/usr/bin/env python
# -----------------------------------------------------------------------
# VIZCOMPLEXMAP
# Copyright 2019, Stephen Gould <stephen.gould@anu.edu.au>
# -----------------------------------------------------------------------
# Code to visualize a complex map (2D array) or flow field represented
# as amplitude and phase.
# -----------------------------------------------------------------------

import numpy as np
import cv2
import matplotlib.pyplot as plt

def viz_map(amplitude, phase, normalize=False):
    """Function to visualize floating point amplitude and phase arrays as RGB images. Phase is
    assumed to be between -pi and pi. Amplitude is assumed to be between 0 and 1."""

    assert amplitude.shape == phase.shape
    assert (phase >= -np.pi).all() and (phase <= np.pi).all()
    assert normalize or (amplitude >= 0.0).all() and  (amplitude <= 1.0).all()

    H, W = amplitude.shape[0], amplitude.shape[1]

    hsv = np.full((H, W, 3), 0, dtype=np.uint8)
    if normalize:
        hsv[..., 2] = cv2.normalize(amplitude, None, 0, 255, cv2.NORM_MINMAX)
    else:
        hsv[..., 2] = (255 * amplitude).astype(np.uint8)
    rgb_amp = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    hsv = np.full((H, W, 3), 255, dtype=np.uint8)
    hsv[..., 0] = 180.0 * (phase + np.pi) / (2.0 * np.pi)
    rgb_phase = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    return rgb_amp, rgb_phase


# -----------------------------------------------------------------------
# Demonstration

if __name__ == "__main__":

    amp = np.zeros((240, 320), dtype=np.float)
    phase = np.zeros((240, 320), dtype=np.float)

    for v in range(amp.shape[0]):
        y = float(v) / amp.shape[0] - 0.5
        for u in range(amp.shape[1]):
            x = float(u) / amp.shape[1] - 0.5
            amp[v, u] = 0.5 * np.sin(8.0 * np.pi * np.sqrt(x ** 2 + y ** 2)) + 0.5
            phase[v, u] = np.arctan2(y, x)

    rgba, rgbp = viz_map(amp, phase)

    plt.figure()
    plt.subplot(1, 3, 1)
    plt.imshow(rgba); plt.xlabel('amplitude')
    plt.subplot(1, 3, 2)
    plt.imshow(rgbp); plt.xlabel('phase')
    plt.subplot(1, 3, 3)

    plt.imshow((rgba / 255.0 * rgbp).astype(np.uint8)); plt.xlabel('combined')
    plt.show()
