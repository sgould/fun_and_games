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

// Draw a triangle path for stroking or filling.
function triangle(ctx, ax, ay, bx, by, cx, cy) {
    ctx.beginPath();
    ctx.moveTo(ax, ay);
    ctx.lineTo(bx, by);
    ctx.lineTo(cx, cy);
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

    // Construct an ANUVidLib object with two canvases for displaying frames and text spans for showing status
    // information. Caches frames every second for faster scrolling (TODO).
    constructor(leftCanvasName, leftSliderName, leftStatusName, rightCanvasName, rightSliderName, rightStatusName) {
        var self = this;

        this.video = document.createElement("video");
        this.leftCanvas = document.getElementById(leftCanvasName);
        this.leftSlider = document.getElementById(leftSliderName);
        this.leftStatus = document.getElementById(leftStatusName);
        this.leftFrame = new Image();
        this.leftFrame.onload = function() { self.redraw(ANUVidLib.LEFT); };

        this.rightCanvas = document.getElementById(rightCanvasName);
        this.rightSlider = document.getElementById(rightSliderName);
        this.rightStatus = document.getElementById(rightStatusName);
        this.rightFrame = new Image();
        this.rightFrame.onload = function() { self.redraw(ANUVidLib.RIGHT); };

        this.frameCache = [];

        this.video.addEventListener('loadeddata', function() {
            self.resize();
            //self.leftFrame = new Image();
            //self.rightFrame = new Image();
            self.leftSlider.max = Math.floor(FPS * self.video.duration);
            self.leftSlider.value = 0;
            self.rightSlider.max = Math.floor(FPS * self.video.duration);
            self.rightSlider.value = 0;
            self.frameCache.length = Math.floor(self.video.duration); // space for 1 frame per second
            self.frameCache.fill(null);
            self.seekTo(0, 0);
        }, false);

        this.video.addEventListener('seeked', function() {
            // extract the frame and redraw
            console.log("updating left frame (" + self.video.videoWidth + ", " + self.video.videoHeight + ")")
            const canvas = document.createElement("canvas");
            canvas.width = self.video.videoWidth;
            canvas.height = self.video.videoHeight;
            canvas.getContext('2d').drawImage(self.video, 0, 0, canvas.width, canvas.height);
            //self.leftFrame.onload = function() { self.redraw(ANUVidLib.LEFT); };
            self.leftFrame.src = canvas.toDataURL("image/jpeg");
        }, false);

        this.resize();
        window.addEventListener('resize', function() { self.resize(); }, false);
    }

    loadVideo(fileURL) {
        this.video.src = fileURL;
    }

    // Seek to a specific index in the video. A negative number means backwards from the end.
    seekTo(leftIndex, rightIndex) {
        console.log("seeking to (" + leftIndex + ", " + rightIndex + ")")

        if (isNaN(this.video.duration)) {
            this.leftStatus.innerHTML = "none";
            this.rightStatus.innerHTML = "none";
            return;
        }

        if (leftIndex < 0) {
            leftIndex = FPS * this.video.duration + leftIndex + 1;
        }
        if (rightIndex < 0) {
            rightIndex = FPS * this.video.duration + rightIndex + 1;
        }

        this.video.currentTime = Math.floor(Math.min(Math.max(0, leftIndex), FPS * this.video.duration), 0) / FPS;
        this.leftStatus.innerHTML = (leftIndex / FPS).toFixed(2) + " / " + this.video.duration.toFixed(2) + "s [" +
            this.video.videoWidth + "-by-" + this.video.videoHeight + "]";
        this.rightStatus.innerHTML = (rightIndex / FPS).toFixed(2) + " / " + this.video.duration.toFixed(2) + "s [" +
            this.video.videoWidth + "-by-" + this.video.videoHeight + "]";
    }

    // Resize canvas when window size changes of new video is loaded.
    resize() {
        this.leftCanvas.width = document.getElementById("leftpanel").clientWidth;
        if (isNaN(this.video.duration)) {
            this.leftCanvas.height = 9 / 16 * this.leftCanvas.width;
        } else {
            console.log(Math.floor(this.leftCanvas.width * this.video.videoHeight / this.video.videoWidth));
            this.leftCanvas.height = Math.floor(this.leftCanvas.width * this.video.videoHeight / this.video.videoWidth);
        }
        this.rightCanvas.width = this.leftCanvas.width;
        this.rightCanvas.height = this.leftCanvas.height;

        this.redraw(ANUVidLib.BOTH);
    }

    // Redraw frames and annotations.
    redraw(side) {
        if (side == ANUVidLib.BOTH) {
            this.redraw(ANUVidLib.LEFT);
            this.redraw(ANUVidLib.RIGHT);
            return;
        }

        console.assert((side == ANUVidLib.LEFT) || (side == ANUVidLib.RIGHT), "invalid side")
        console.log("redrawing " + side)

        // draw left frame
        if (side == ANUVidLib.LEFT) {
            var context = this.leftCanvas.getContext('2d');
            context.drawImage(this.leftFrame, 0, 0, this.leftCanvas.width, this.leftCanvas.height);

            // draw border
            context.lineWidth = 7; context.strokeStyle = "#ffffff";
            roundedRect(context, 0, 0, this.leftCanvas.width, this.leftCanvas.height, 9);
            context.stroke();
            context.lineWidth = 5; context.strokeStyle = "#000000";
            context.strokeRect(0, 0, this.leftCanvas.width, this.leftCanvas.height);
            roundedRect(context, 0, 0, this.leftCanvas.width, this.leftCanvas.height, 9);
            context.stroke();
        }

        // draw right frame
        // TODO: remove replicated code
    }
}

/*
** In-browser Video Labeler. Responsible to rendering and user I/O. In particular,
** responds to the video slider, draws the filmstrips and current frame, shows status
** information and handles annotation.
*/
class WebVidLib {
    // Construct a WebVidLib object with a canvas for displaying frames and an
    // text span for showing status information.
    constructor(canvasName, sliderName, statusName) {
        this.video = document.createElement("video");
        this.offScreenCanvas = document.createElement("canvas");
        this.offScreenCanvas.width = 96; this.offScreenCanvas.height = 72;

        this.canvas = document.getElementById(canvasName);
        this.slider = document.getElementById(sliderName);
        this.status = document.getElementById(statusName);
        this.frames = [];

        var self = this;
        this.video.addEventListener('loadeddata', function() {
            self.slider.max = Math.floor(FPS * self.video.duration);
            self.slider.value = "0";
            self.frames.length = self.slider.max;
            self.frames.fill(null);
            self.seekTo(0);
        }, false);

        this.video.addEventListener('seeked', function() {
            // extract the frame at the current index and redraw the filmstrip
            console.log("seeked event: " + self.video.currentTime);
            var indx = Math.floor(FPS * self.video.currentTime);
            self.extractFrame(indx);
            self.drawFilmStrip(indx, 5);
        }, false);
    }

    // Extract and compress frame from the video.
    extractFrame(indx) {
        if (this.frames[indx] != null) {
            console.log(this.frames[indx]);
            return;
        }
        var ctx = this.offScreenCanvas.getContext('2d');
        ctx.drawImage(this.video, 0, 0, this.offScreenCanvas.width, this.offScreenCanvas.height);
        this.frames[indx] = this.offScreenCanvas.toDataURL("image/jpeg");
    }

    // Draw filmstrip centered on index and +/- window.
    drawFilmStrip(indx, window) {
        var numFrames = 2 * window + 1;
        var startFrame = indx - window;
        var dx = this.canvas.width / numFrames;

        //console.log(this.frames.length);

        // draw each frame
        var context = this.canvas.getContext('2d');
        context.lineWidth = 3;
        context.fillStyle = "#ffffff";
        for (var i = 0; i < numFrames; i++) {
            // TODO: replace with extracting from an array
            if ((startFrame + i < 0) || (startFrame + i > Math.floor(FPS * this.video.duration))) {
                console.log("cross " + (startFrame + i));
                context.fillRect(i * dx, 0, dx, this.canvas.height);
                context.strokeStyle = "#ff0000";
                context.beginPath();
                context.moveTo(i * dx, 0);
                context.lineTo(i * dx + dx, this.canvas.height);
                context.moveTo(i * dx + dx, 0);
                context.lineTo(i * dx, this.canvas.height);
                context.stroke();
            } else if (this.frames[startFrame + i] != null) {
                console.log("drawing existing " + (startFrame + i));
                const image = new Image();

                var helper = function(_i, _dx, _dy) {
                    return function() {
                        context.imageSmoothingEnabled = false;
                        context.drawImage(image, _i * _dx, 0, _dx, _dy);
                        console.log(_i);

                        context.lineWidth = 3;
                        context.strokeStyle = "#000000";
                        context.strokeRect(_i * _dx,  1, _dx, _dy - 2);
                        roundedRect(context, _i * _dx, 1, _dx, _dy - 2, 7);
                        context.stroke();

                        if (_i == window) {
                            context.strokeStyle = "#ffffff";
                            context.fillStyle = "#000000";
                            triangle(context, _i * _dx + _dx / 2, 5, _i * _dx + _dx / 2 + 5, 0, _i * _dx + _dx / 2 - 5, 0);
                            context.stroke(); context.fill();
                            triangle(context, _i * _dx + _dx / 2, _dy - 5, _i * _dx + _dx / 2 + 5, _dy, _i * _dx + _dx / 2 - 5, _dy);
                            context.stroke(); context.fill();
                        }
                    }
                }
                image.onload = helper(i, dx, this.canvas.height);

                console.log("drawing existing " + this.frames[startFrame + i]);
                image.src = this.frames[startFrame + i];
            } else {
                console.log("current frame " + (startFrame + i));
                // TODO
                //context.drawImage(this.video, i * dx, 0, dx, this.canvas.height);
                console.log("cross " + (startFrame + i));
                context.fillRect(i * dx, 0, dx, this.canvas.height);
                context.strokeStyle = "#00ff00";
                context.beginPath();
                context.moveTo(i * dx, 0);
                context.lineTo(i * dx + dx, this.canvas.height);
                context.moveTo(i * dx + dx, 0);
                context.lineTo(i * dx, this.canvas.height);
                context.stroke();
            }

            context.strokeStyle = "#000000";
            context.strokeRect(i * dx,  1, dx, this.canvas.height - 2);
            roundedRect(context, i * dx, 1, dx, this.canvas.height - 2, 7);
            context.stroke();
        }

        // draw indicator on center frame
        var cx = window * dx + dx / 2;
        context.strokeStyle = "#ffffff";
        context.fillStyle = "#000000";
        triangle(context, cx, 5, cx + 5, 0, cx - 5, 0);
        context.stroke(); context.fill();
        triangle(context, cx, this.canvas.height - 5, cx + 5, this.canvas.height, cx - 5, this.canvas.height);
        context.stroke(); context.fill();
    }

    loadVideo(fileURL) {
        this.video.src = fileURL;
    }

    // Seek to a specific index in the video. A negative number means backwards from the end.
    seekTo(index) {
        if (isNaN(this.video.duration)) {
            this.status.innerHTML = "none";
            return;
        }

        if (index < 0) {
            index = FPS * this.video.duration + index + 1;
        }

        if (this.frames[index] != null) {
            this.drawFilmStrip(index, 5);
        } else {
            this.video.currentTime = Math.floor(Math.min(Math.max(0, index), FPS * this.video.duration), 0) / FPS;
            console.log("seekTo: " + this.video.currentTime);
        }
        this.status.innerHTML = (index / FPS).toFixed(2) + " / " + this.video.duration.toFixed(2) + "s";
    }

    // Seek to a location in the video relative to the current location.
    seekAdv(inc) {
        return this.seekTo(FPS * this.video.currentTime + inc);
    }
}
