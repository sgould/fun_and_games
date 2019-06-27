#!/usr/bin/env python
#
# Script to fetch Google Scholar pages from a CSV list of Google Scholar IDs and plot citations by grouping. Expects
# CSV data in the form of:
#  <name>, <grouping>, <scholarID>
#
# For example:
#  Stephen Gould, D, YvdzeM8AAAAJ
#

import os
import csv
import re
import numpy as np
import urllib.request
from plot_citations import GoogleScholarHTMLParser

import tkinter as tk
from tkinter import messagebox, filedialog

HTML_DIR = "gs_cache"
URL_TEMPLATE = r"https://scholar.google.com.au/citations?user={}&hl=en"

app_wnd = tk.Tk()
app_wnd.withdraw() # hide application window
CSV_FILE = tk.filedialog.askopenfilename(title="Scholar IDs", filetypes=(("CVS Files", "*.csv"), ("All Files", "*.*")))
if not CSV_FILE: exit(0)
OVERWRITE = tk.messagebox.askyesno("Overwrite", "Do you wish to overwrite existing data?")

if not os.path.isdir(HTML_DIR):
    os.makedirs(HTML_DIR)

# fetch Google Scholar pages
with open(CSV_FILE, 'rt', encoding='utf8') as file:
    reader = csv.reader(file, skipinitialspace=True)
    next(reader, None) # skip header
    for name, grouping, gs_id in reader:
        if len(gs_id) == 0:
            continue
        cache_filename = os.path.join(HTML_DIR, "{}.html".format(gs_id))
        if OVERWRITE or not os.path.exists(cache_filename):
            url = URL_TEMPLATE.format(gs_id)

            print("Fetching URL {}...".format(url))
            try:
                response = urllib.request.urlopen(url)
                html = str(response.read())
                response.close()

                html = re.sub("\\\\t|\\\\r\\\\n", "", html)
                with open(cache_filename, 'wt') as outfile:
                    outfile.write(html)
            except:
                print("ERROR: could not retrieve or update data for {}".format(name))

# process Google Scholar pages
data = {}
with open(CSV_FILE, 'rt', encoding='utf8') as file:
    reader = csv.reader(file, skipinitialspace=True)
    next(reader, None)  # skip header
    for name, grouping, gs_id in reader:
        cache_filename = os.path.join(HTML_DIR, "{}.html".format(gs_id))
        if not os.path.exists(cache_filename):
            print("WARNING: missing data for {}".format(name))
            continue
        with open(cache_filename, 'rt') as infile:
            html = infile.read()

        parser = GoogleScholarHTMLParser()
        parser.feed(html)
        #print("{:5d} {:5d} {}".format(parser.citeSummaryData[0], parser.citeSummaryData[1], parser.citeCounts[-1], name))

        grouping = grouping[0]
        if grouping not in data:
            data[grouping] = []
        data[grouping].append((parser.citeSummaryData[0], parser.citeSummaryData[1],  parser.citeCounts[-1], name))

for key in sorted(data.keys()):
    print("Career median for grouping {} is {}".format(key, np.median([v[0] for v in data[key]])))

for key in sorted(data.keys()):
    print("Last 5-years median for grouping {} is {}".format(key, np.median([v[1] for v in data[key]])))

x, y1, y2, y3, n = [], [], [], [], []
for key in sorted(data.keys()):
    data[key] = sorted(data[key])
    x += [key] * len(data[key])
    y1 += [v[0] for v in data[key]]
    y2 += [v[1] for v in data[key]]
    y3 += [v[2] for v in data[key]]
    n += [v[3] for v in data[key]]

import seaborn as sea
import matplotlib.pyplot as plt
sea.set(font_scale=1.2)

plt.figure()
width = 0.8
plt.bar(np.linspace(0, len(y1), len(y1)), y1, width)
plt.bar(np.linspace(0, len(y2), len(y2)), y2, width, color=[0.8, 0.0, 0.0])
plt.bar(np.linspace(0, len(y3), len(y3)), y3, width, color=[0.0, 0.8, 0.0])
if 0:
    plt.xticks(np.linspace(0, len(x), len(x)) + 0.5 * width, x)
    plt.xlabel('Researcher (Group)'); plt.ylabel('Citations')
else:
    plt.xticks(np.linspace(0, len(x), len(x)) + 0.5 * width, n)
    plt.xlabel('Researcher (Name)'); plt.ylabel('Citations')
    plt.xticks(rotation=90)

plt.legend(['Total', 'Last 5 Years', 'Current Year'])
plt.show()
