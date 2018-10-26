#!/usr/bin/env python3
#
# Script to extract and plot Google Scholar citations. Useful for reporting track record in grant applications, etc.
#

import urllib.request
from html.parser import HTMLParser
import re

import seaborn as sea
import matplotlib.pyplot as plt
sea.set(font_scale=1.2)


# Google Scholar page to process
URL = r"https://scholar.google.com.au/citations?user=YvdzeM8AAAAJ&hl=en"

print("Fetching Google Scholar page...")
response = urllib.request.urlopen(URL)
html = str(response.read())
response.close()

html = re.sub("\\\\t|\\\\r\\\\n", "", html)


class GoogleScholarHTMLParser(HTMLParser):
    """Parser to extract citation information from Google Scholar page."""

    insideSpan = False
    spanClass = None
    years = []
    citeCounts = []

    def handle_starttag(self, tag, attrs):
        if (tag == "span"):
            self.insideSpan = True
            for (key, val) in attrs:
                if 'class' in key:
                    self.spanClass = val
                    break

    def handle_data(self, data):
        if self.insideSpan:
            if 'gsc_g_t' in self.spanClass:
                self.years.append(int(data.strip()))
            if 'gsc_g_al' in self.spanClass:
                self.citeCounts.append(int(data.strip()))

    def handle_endtag(self, tag):
        if (tag == "span"):
            self.insideSpan = False
            self.spacClass = None


print("Parsing HTML...")
parser = GoogleScholarHTMLParser()
parser.feed(html)

print("Plotting...")

plt.figure()
width = 0.8
plt.bar(parser.years, parser.citeCounts, width)
plt.plot([year + 0.5 * width for year in parser.years], parser.citeCounts, 'ro-', lw=2)
plt.xticks([year + 0.5 * width for year in parser.years], parser.years)
plt.xlabel('Year'); plt.ylabel('Citations')
plt.show()
