#!/usr/bin/env python
#
# Script to extract and plot Google Scholar citations. Useful for reporting track record in grant applications, etc.
#

import urllib.request
from html.parser import HTMLParser
import re

import seaborn as sea
import matplotlib.pyplot as plt
sea.set(font_scale=1.2)

from datetime import datetime
import numpy as np

class GoogleScholarHTMLParser(HTMLParser):
    """Parser to extract citation information from Google Scholar page."""

    def __init__(self):
        super(GoogleScholarHTMLParser, self).__init__()

        self.insideSpanClass = []
        self.insideTdClass = []
        self.citeYears = []
        self.citeCounts = []
        self.citeSummaryData = []

    @staticmethod
    def get_attr(attrs, key='class'):
        for (k, v) in attrs:
            if k == key:
                return v

        return None

    def handle_starttag(self, tag, attrs):
        if (tag == 'span'):
            self.insideSpanClass.append(self.get_attr(attrs, 'class'))
        if (tag == 'td'):
            self.insideTdClass.append(self.get_attr(attrs, 'class'))

    def handle_data(self, data):
        if len(self.insideSpanClass) > 0:
            if self.insideSpanClass[-1] == 'gsc_g_t':
                self.citeYears.append(int(data.strip()))
            if self.insideSpanClass[-1] == 'gsc_g_al':
                self.citeCounts.append(int(data.strip()))
        if len(self.insideTdClass) > 0:
            if self.insideTdClass[-1] == 'gsc_rsb_std':
                self.citeSummaryData.append(int(data.strip()))

    def handle_endtag(self, tag):
        if (tag == 'span'):
            self.insideSpanClass.pop()
        if (tag == 'td'):
            self.insideTdClass.pop()


def bar_plot_with_trend(years, counts, prediction=None, width=0.8):
    """Generate a bar plot showing trend line and optional prediction."""

    if prediction is not None:
        plt.bar(years[-1], prediction, width, align='center', color=[1.0, 1.0, 1.0])
        plt.plot([year for year in years[-2:]], [counts[-2], prediction], 'ko--', lw=2)

    plt.bar(years, counts, width, color=[0.75, 0.75, 0.75])
    plt.plot(years, counts, 'ko-', lw=2)
    plt.xticks(years, years)


if __name__ == "__main__":

    # default Google Scholar page to process
    URL = r"https://scholar.google.com.au/citations?user=YvdzeM8AAAAJ&hl=en"

    # request user input for Google Scholar URL
    import tkinter as tk
    from tkinter import simpledialog

    app_wnd = tk.Tk()
    app_wnd.withdraw()
    URL = simpledialog.askstring("Plot Citations", "Enter the full URL for the Google Scholar page you wish to plot:",
                                 initialvalue=URL, parent=app_wnd)
    if URL is None:
        exit(0)

    # fetch Google Scholar page and extract statistics
    print("Fetching Google Scholar page...")
    response = urllib.request.urlopen(URL)
    html = str(response.read())
    response.close()

    html = re.sub("\\\\t|\\\\r\\\\n", "", html)

    print("Parsing HTML...")
    parser = GoogleScholarHTMLParser()
    parser.feed(html)
    print("...{} total citations".format(parser.citeSummaryData[0]))
    #print(parser.citeCounts)

    year_fraction = datetime.now().timetuple().tm_yday / 365.0
    if datetime.now().timetuple().tm_year > parser.citeYears[-1]:
        print("{:0.1f}% of year with no data for this year".format(100.0 * year_fraction))
        year_prediction = None
    else:
        year_prediction = int(parser.citeCounts[-1] / year_fraction)
        print("{:0.1f}% of year with {} citations ({} predicted)".format(100.0 * year_fraction, parser.citeCounts[-1], year_prediction))

    print("Plotting Citations...")

    plt.figure()

    plt.subplot(2, 1, 1)
    bar_plot_with_trend(parser.citeYears, parser.citeCounts, year_prediction)
    plt.xlabel('Year'); plt.ylabel('Citations per Year')

    plt.subplot(2, 1, 2)
    counts = np.cumsum(parser.citeCounts)
    bar_plot_with_trend(parser.citeYears, counts, None if year_prediction is None else year_prediction + counts[-2])
    plt.xlabel('Year'); plt.ylabel('Total Citations')

    plt.tight_layout(pad=0.2)
    plt.show()
