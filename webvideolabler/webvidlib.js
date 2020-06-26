/*******************************************************************************
** WEBVIDLIB: A Javascript library for web-based video annotation.
**
** Copyright (C) 2020, Stephen Gould <stephen.gould@anu.edu.au>
*******************************************************************************/

class WebVidLib {
    // Construct a WebVidLib object with a canvas for displaying frames and an
    // text span for showing status information.
    constructor(canvasName, statusName) {
        this.video = document.createElement("video");
        this.canvas = document.getElementById(canvasName);
        this.status = document.getElementById(statusName);

        var self = this;
        this.video.addEventListener('loadeddata', function() {
            self.seekTo(0);
        }, false);

        this.video.addEventListener('seeked', function() {
            var context = self.canvas.getContext('2d');
            context.drawImage(self.video, 0, 0, self.canvas.width, self.canvas.height);
        }, false);
    }

    loadVideo(fileURL) {
        this.video.src = fileURL;
    }

    // Seek to a random location in the video
    seekRandom() {
        if (!isNaN(this.video.duration)) {
            var rand = Math.round(Math.random() * this.video.duration * 1000) + 1;
            this.video.currentTime = rand / 1000;
            this.status.innerHTML = this.video.currentTime.toString() + " / " + this.video.duration.toString() + "s";
        }
    }

    // Seek to a specific location in the video. A negative number means backwards from the end.
    seekTo(location) {
        if (isNaN(this.video.duration)) {
            this.status.innerHTML = "none";
            return;
        }

        if (location < 0) {
            location = this.video.duration + location + 1;
        }
        this.video.currentTime = Math.floor(Math.min(Math.max(0, location), this.video.duration), 0);
        this.status.innerHTML = this.video.currentTime.toString() + " / " + this.video.duration.toString() + "s";
    }

    // Seek to a location in the video relative to the current location.
    seekAdv(inc) {
        return this.seekTo(this.video.currentTime + inc);
    }
}
