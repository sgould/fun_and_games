#!/usr/bin/env python
#
# Script to extract and plot Google Scholar citations. Useful for reporting track record in grant applications, etc.
#

import urllib.request
from html.parser import HTMLParser
import re

import seaborn as sea
import matplotlib.pyplot as plt
sea.set(font_scale=1.4)

from datetime import datetime


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
        year_prediction = 0
    else:
        year_prediction = int(parser.citeCounts[-1] / year_fraction)
        print("{:0.1f}% of year with {} citations ({} predicted)".format(100.0 * year_fraction, parser.citeCounts[-1], year_prediction))

    print("Plotting Citations...")

    plt.figure()
    width = 0.8

    plt.bar(parser.citeYears[-1], year_prediction, width, color=[1.0, 1.0, 1.0])
    plt.plot([year + 0.5 * width for year in parser.citeYears[-2:]], [parser.citeCounts[-2], year_prediction], 'ko--', lw=2)

    plt.bar(parser.citeYears, parser.citeCounts, width, color=[0.75, 0.75, 0.75])
    plt.plot([year + 0.5 * width for year in parser.citeYears], parser.citeCounts, 'ko-', lw=2)
    plt.xticks([year + 0.5 * width for year in parser.citeYears], parser.citeYears)
    plt.xlabel('Year'); plt.ylabel('Citations')
    plt.tight_layout(pad=0.2)
    plt.show()
