#!/usr/bin/env python
#
# Script to replace img tags in html source with embedded base64 images.
#

import sys
import re
import base64

prog = re.compile(r'[^\']<img\s+src="([^"]+)"[^>]*>')

for line in sys.stdin:
    # look for img tags
    match = prog.search(line)
    if match:
        # extract the img src text
        imgsrc = match.group(1)
        if (len(imgsrc) > 4) and (imgsrc[0:4] == "data"):
            continue

        # encode the image as bas64
        with open(imgsrc, "rb") as img:
            data = base64.b64encode(img.read())

        # replace the img src string
        data = "data:image/png;base64," + data.decode('utf-8')
        line = line.replace(match.group(1), data)

    # print the line
    print(line.rstrip())
