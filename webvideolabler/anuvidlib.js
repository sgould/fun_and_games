/*******************************************************************************
** ANUVIDLIB: A Javascript library for web-based video annotation.
** Copyright (C) 2020, Stephen Gould <stephen.gould@anu.edu.au>
**
** TODO:
**  1. add caching of extracted frames (reduced size)
**  2. configuration of temporal and spatial resolutions
**  3. button to export frames
*******************************************************************************/

const FPS = 10;     // temporal resolution (frames per second)

/*
** Drawing utilities.
*/

// Draw a rounded rectangle path for stroking or filling.
function roundedRect(ctx, x, y, width, height, rounded) {
    const radiansInCircle = 2 * Math.PI
    const halfRadians = (2 * Math.PI) / 2
    const quarterRadians = (2 * Math.PI) / 4

    ctx.beginPath();
    ctx.arc(rounded + x, rounded + y, rounded, -quarterRadians, halfRadians, true);
    ctx.lineTo(x, y + height - rounded);
    ctx.arc(rounded + x, height - rounded + y, rounded, halfRadians, quarterRadians, true);
    ctx.lineTo(x + width - rounded, y + height);
    ctx.arc(x + width - rounded, y + height - rounded, rounded, quarterRadians, 0, true);
    ctx.lineTo(x + width, y + rounded);
    ctx.arc(x + width - rounded, y + rounded, rounded, 0, -quarterRadians, true);
    ctx.lineTo(x + rounded, y);
    ctx.closePath();
}

/*
** In-browser Video Labeler. Responsible for video rendering and user I/O.
*/
class ANUVidLib {
    // Constants.
    static get LEFT() { return 0; }
    static get RIGHT() { return 1; }
    static get BOTH() { return -1; }
    static get NONE() { return -2; }

    // Construct an ANUVidLib object with two canvases for displaying frames and text spans for showing status
    // information. Caches frames every second for faster scrolling (TODO).
    constructor(leftCanvasName, leftSliderName, leftStatusName, rightCanvasName, rightSliderName, rightStatusName) {
        var self = this;

        this.video = document.createElement("video");

        this.leftPanel = {
            side: ANUVidLib.LEFT,
            canvas: document.getElementById(leftCanvasName),
            slider: document.getElementById(leftSliderName),
            status: document.getElementById(leftStatusName),
            frame: new Image(),
            timestamp: null
        };
        this.leftPanel.frame.onload = function() { self.redraw(ANUVidLib.LEFT); };

        this.rightPanel = {
            side: ANUVidLib.RIGHT,
            canvas: document.getElementById(rightCanvasName),
            slider: document.getElementById(rightSliderName),
            status: document.getElementById(rightStatusName),
            frame: new Image(),
            timestamp: null
        };
        this.rightPanel.frame.onload = function() { self.redraw(ANUVidLib.RIGHT); };

        this.frameCache = [];

        this.vidRequestQ = []; // video queries (timestamp, who)

        this.video.addEventListener('loadeddata', function() {
            self.resize();
            self.leftPanel.slider.max = Math.floor(FPS * self.video.duration);
            self.leftPanel.slider.value = 0;
            self.leftPanel.timestamp = null;
            self.rightPanel.slider.max = Math.floor(FPS * self.video.duration);
            self.rightPanel.slider.value = 0;
            self.rightPanel.timestamp = null;
            self.frameCache.length = Math.floor(self.video.duration); // space for 1 frame per second
            self.frameCache.fill(null);
            self.seekTo(0, 0);
        }, false);

        this.video.addEventListener('seeked', function() {
            // extract the frame and redraw (triggered by onload)
            const canvas = document.createElement("canvas");
            canvas.width = self.video.videoWidth;
            canvas.height = self.video.videoHeight;
            canvas.getContext('2d').drawImage(self.video, 0, 0, canvas.width, canvas.height);

            // update the correct panel
            console.assert(self.vidRequestQ.length > 0, "something went wrong");
            if (self.vidRequestQ[0].who == ANUVidLib.LEFT) {
                self.leftPanel.frame.src = canvas.toDataURL("image/jpeg");
            } else if (self.vidRequestQ[0].who == ANUVidLib.RIGHT) {
                self.rightPanel.frame.src = canvas.toDataURL("image/jpeg");
            }

            // cache frame if on one second boundary
            if (self.video.currentTime == Math.floor(self.video.currentTime)) {
                //console.log("caching frame at " + self.video.currentTime + " seconds");
                self.frameCache[self.video.currentTime] = canvas.toDataURL("image/jpeg");
            }

            // trigger next video query if there is one
            self.vidRequestQ.shift();
            if (self.vidRequestQ.length > 0) {
                self.video.currentTime = self.vidRequestQ[0].timestamp;
            }
        }, false);

        this.resize();
        window.addEventListener('resize', function() { self.resize(); }, false);
    }

    loadVideo(fileURL) {
        this.video.src = fileURL;
    }

    // Seek to a specific index in the video. A negative number means don't update.
    seekTo(leftIndex, rightIndex) {
        if (isNaN(this.video.duration)) {
            this.leftPanel.status.innerHTML = "none";
            this.rightPanel.status.innerHTML = "none";
            return;
        }

        this.vidRequestQ = []
        if (leftIndex >= 0) {
            const index = Math.floor(Math.min(Math.max(0, leftIndex), FPS * this.video.duration), 0);
            const ts = index / FPS;
            if ((index % FPS == 0) && (this.frameCache[ts] != null)) {
                this.leftPanel.frame.src = this.frameCache[ts];
            } else {
                this.vidRequestQ.push({timestamp: ts, who: ANUVidLib.LEFT});
            }

            this.leftPanel.timestamp = ts;
            this.leftPanel.status.innerHTML = ts.toFixed(2) + " / " + this.video.duration.toFixed(2) + "s [" +
                this.video.videoWidth + "-by-" + this.video.videoHeight + "]";
        }

        if (rightIndex >= 0) {
            const index = Math.floor(Math.min(Math.max(0, rightIndex), FPS * this.video.duration), 0);
            const ts = index / FPS;
            if ((index % FPS == 0) && (this.frameCache[ts] != null)) {
                this.rightPanel.frame.src = this.frameCache[ts];
            } else {
                this.vidRequestQ.push({timestamp: ts, who: ANUVidLib.RIGHT});
            }

            this.rightPanel.timestamp = ts;
            this.rightPanel.status.innerHTML = ts.toFixed(2) + " / " + this.video.duration.toFixed(2) + "s [" +
                this.video.videoWidth + "-by-" + this.video.videoHeight + "]";
        }

        // add remaining frames at one-second boundaries for caching
        for (var i = 0; i < this.video.duration; i++) {
            if (this.frameCache[i] == null) {
                this.vidRequestQ.push({timestamp: i, who: ANUVidLib.NONE});
            }
        }

        // trigger first video request
        if (this.vidRequestQ.length > 0) {
            this.video.currentTime = this.vidRequestQ[0].timestamp;
        }
    }

    // Resize left and right canvas when window size changes of new video is loaded.
    resize() {
        this.leftPanel.canvas.width = this.leftPanel.canvas.parentNode.clientWidth;
        if (isNaN(this.video.duration)) {
            this.leftPanel.canvas.height = 9 / 16 * this.leftPanel.canvas.width;
        } else {
            this.leftPanel.canvas.height = Math.floor(this.leftPanel.canvas.width * this.video.videoHeight / this.video.videoWidth);
        }
        this.rightPanel.canvas.width = this.leftPanel.canvas.width;
        this.rightPanel.canvas.height = this.leftPanel.canvas.height;

        this.redraw(ANUVidLib.BOTH);
    }

    // Redraw frames and annotations. Parameter 'side' can be LEFT, RIGHT or BOTH.
    redraw(side) {
        if (side == ANUVidLib.BOTH) {
            this.redraw(ANUVidLib.LEFT);
            this.redraw(ANUVidLib.RIGHT);
            return;
        }

        console.assert((side == ANUVidLib.LEFT) || (side == ANUVidLib.RIGHT), "invalid side")

        // draw left frame
        if (side == ANUVidLib.LEFT) {
            this.paint(this.leftPanel);
        }

        // draw right frame
        if (side == ANUVidLib.RIGHT) {
            this.paint(this.rightPanel);
        }
    }

    // Draw a frame and it's annotations.
    paint(panel) {
        var context = panel.canvas.getContext('2d');
        context.drawImage(panel.frame, 0, 0, panel.canvas.width, panel.canvas.height);

        // draw border
        context.lineWidth = 7; context.strokeStyle = "#ffffff";
        roundedRect(context, 0, 0, panel.canvas.width, panel.canvas.height, 9);
        context.stroke();
        context.lineWidth = 5; context.strokeStyle = "#000000";
        context.strokeRect(0, 0, panel.canvas.width, panel.canvas.height);
        roundedRect(context, 0, 0, panel.canvas.width, panel.canvas.height, 9);
        context.stroke();
    }
}
