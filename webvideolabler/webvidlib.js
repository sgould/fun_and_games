/*******************************************************************************
** WEBVIDLIB: A Javascript library for web-based video annotation.
**
** Copyright (C) 2020, Stephen Gould <stephen.gould@anu.edu.au>
**
** TODO:
**  1. add caching of extracted frames (reduced size)
**  2. configuration of temporal and spatial resolutions
**  3. button to export frames
*******************************************************************************/

const FPS = 10;    // temporal resolution (frames per second)

class WebVidLib {
    // Construct a WebVidLib object with a canvas for displaying frames and an
    // text span for showing status information.
    constructor(canvasName, sliderName, statusName) {
        this.video = document.createElement("video");
        this.canvas = document.getElementById(canvasName);
        this.slider = document.getElementById(sliderName);
        this.status = document.getElementById(statusName);

        var self = this;
        this.video.addEventListener('loadeddata', function() {
            self.slider.max = Math.floor(FPS * self.video.duration);
            self.slider.value = "0";
            self.seekTo(0);
        }, false);

        this.video.addEventListener('seeked', function() {
            var context = self.canvas.getContext('2d');
            var dx = self.canvas.width / 11;
            context.lineWidth = 3;
            context.strokeStyle = "#000000";
            for (var i = 0; i < 11; i++) {
                context.drawImage(self.video, i * dx, 0, dx, self.canvas.height);
                context.strokeRect(i * dx,  0, dx, self.canvas.height);
            }

            context.strokeStyle = "#0000ff";
            context.lineWidth = 5;
            context.strokeRect(5 * dx, 2, dx, self.canvas.height - 4);
            context.strokeStyle = "#ffffff";
            context.lineWidth = 1;
            context.strokeRect(5 * dx,  2, dx, self.canvas.height - 4);
        }, false);
    }

    loadVideo(fileURL) {
        this.video.src = fileURL;
    }

    // Seek to a specific location in the video. A negative number means backwards from the end.
    seekTo(location) {
        if (isNaN(this.video.duration)) {
            this.status.innerHTML = "none";
            return;
        }

        console.log(location);
        if (location < 0) {
            location = FPS * this.video.duration + location + 1;
        }
        this.video.currentTime = Math.floor(Math.min(Math.max(0, location), FPS * this.video.duration), 0) / FPS;
        this.status.innerHTML = this.video.currentTime.toFixed(2) + " / " + this.video.duration.toFixed(2) + "s";
    }

    // Seek to a location in the video relative to the current location.
    seekAdv(inc) {
        return this.seekTo(FPS * this.video.currentTime + inc);
    }
}
