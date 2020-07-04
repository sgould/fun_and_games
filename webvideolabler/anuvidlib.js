/*******************************************************************************
** ANUVIDLIB: A Javascript library for browser-based video annotation.
** Copyright (C) 2020, Stephen Gould <stephen.gould@anu.edu.au>
**
*******************************************************************************/

/*
TODO:
    X1. resize and redraw left and right canvas with window
    X2. rounded rectangle boundary
    X3. left/right tracking
    X4. buffer video frames every second for faster scrolling
    X5. save configuration locally
    6. help page/video tutorial
    7. annotation functionality (types: temporal segments, bounding boxes, segments); define fields
    8. load/save annotations
    9. export frames
    10. annotation visualisation (e.g., segments, tracks) and search
    X11. style sheet
    12. test in different browsers
    X13. fixed timestamp rounding bug
    14. annotation copying
    X15. keyboard shortcuts
    16. tidy up and error checking
    17. warn on delete
    18. keyframes (load/save, add, navigate)
    19. proper modules and imports
*/

/*
** Configuration.
*/

const VERSION = "0.1(alpha)"    // library version (useful for loading old file formats)
const FPS = 10;                 // temporal resolution (frames per second)

// webpage control ids
const LEFTCANVASNAME  = "leftframe";
const LEFTSLIDERNAME  = "leftslider";
const LEFTSTATUSNAME  = "leftstatus";
const LEFTOBJLISTNAME  = null; // TODO

const RIGHTCANVASNAME = "rightframe";
const RIGHTSLIDERNAME = "rightslider";
const RIGHTSTATUSNAME = "rightstatus";
const RIGHTOBJLISTNAME = null; // TODO

const VIDSEGTABLENAME = "vidsegtable";

/*
** Control callback utilities.
*/

// defocus the current control element when enter is pressed and move focus to target element
function defocusOnEnter(event, target = null) {
    if (event.keyCode == 13 || event.which == 13) {
        event.currentTarget.blur();
        if (target != null) {
            target.focus();
        }
    }
}

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
** Mouse drag context helper.
*/

class DragContext {
    // Drag mode.
    static get NONE() { return 0;}
    static get MOVING() { return 1; }
    static get SIZING() { return 2; }

    constructor() {
        this.mode = DragContext.NONE;
        this.startX = null;
        this.startY = null;
        this.anchor = null;
    }
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

    // Properties.
    get greyframes() { return this._greyframes; }
    set greyframes(value) { this._greyframes = value; this.redraw(); }
    get tiedframes() { return this._tiedframes; }
    set tiedframes(value) { this._tiedframes = value; }

    // Construct an ANUVidLib object with two canvases for displaying frames and text spans for showing status
    // information. Caches frames every second for faster feedback during scrubbing.
    constructor() {
        var self = this;

        this._greyframes = false;
        this._tiedframes = false;
        this.video = document.createElement("video");

        this.leftPanel = {
            side: ANUVidLib.LEFT,
            canvas: document.getElementById(LEFTCANVASNAME),
            slider: document.getElementById(LEFTSLIDERNAME),
            status: document.getElementById(LEFTSTATUSNAME),
            frame: new Image(),
            timestamp: null
        };
        this.leftPanel.frame.onload = function() { self.redraw(ANUVidLib.LEFT); };
        this.leftPanel.canvas.onmousemove = function(e) { self.mousemove(e, ANUVidLib.LEFT); }
        this.leftPanel.canvas.onmouseout = function(e) { self.mouseout(e, ANUVidLib.LEFT); }
        this.leftPanel.canvas.onmousedown = function(e) { self.mousedown(e, ANUVidLib.LEFT); }
        this.leftPanel.canvas.onmouseup = function(e) { self.mouseup(e, ANUVidLib.LEFT); }

        this.rightPanel = {
            side: ANUVidLib.RIGHT,
            canvas: document.getElementById(RIGHTCANVASNAME),
            slider: document.getElementById(RIGHTSLIDERNAME),
            status: document.getElementById(RIGHTSTATUSNAME),
            frame: new Image(),
            timestamp: null
        };
        this.rightPanel.frame.onload = function() { self.redraw(ANUVidLib.RIGHT); };
        this.rightPanel.canvas.onmousemove = function(e) { self.mousemove(e, ANUVidLib.RIGHT); }
        this.rightPanel.canvas.onmouseout = function(e) { self.mouseout(e, ANUVidLib.RIGHT); }
        this.rightPanel.canvas.onmousedown = function(e) { self.mousedown(e, ANUVidLib.RIGHT); }
        this.rightPanel.canvas.onmouseup = function(e) { self.mouseup(e, ANUVidLib.RIGHT); }

        this.objectList = [[]];
        this.activeObject = null;
        this.dragContext = new DragContext();

        this.bFrameCacheComplete = false;
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

            self.objectList.length = Math.floor(FPS * self.video.duration);
            for (var i = 0; i < self.objectList.length; i++) {
                self.objectList[i] = [];
            }

            self.frameCache.length = Math.floor(self.video.duration); // space for 1 frame per second
            self.frameCache.fill(null);
            self.bFrameCacheComplete = false;

            self.seekToIndex(0, 0);
        }, false);

        this.video.addEventListener('error', function() {
            window.alert("ERROR: could not load video \"" + self.video.src + "\"");
            self.frameCache = [];
            self.objectList = [];
            self.leftPanel.frame = new Image();
            self.leftPanel.frame.onload = function() { self.redraw(ANUVidLib.LEFT); };
            self.rightPanel.frame = new Image();
            self.rightPanel.frame.onload = function() { self.redraw(ANUVidLib.RIGHT); };
            self.redraw(ANUVidLib.BOTH);
            self.leftPanel.status.innerHTML = "none";
            self.rightPanel.status.innerHTML = "none";
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

    // Load a new video file. Resets data once loaded.
    loadVideo(fileURL) {
        this.video.src = fileURL;
        clearclips();
    }

    // Convert between indices and timestamps.
    indx2time(index) { return index / FPS; }
    time2indx(timestamp) { return Math.round(FPS * timestamp); }

    // Seek to a specific index in the video. A negative number means don't update unless tied.
    seekToIndex(leftIndex, rightIndex) {
        console.assert((leftIndex >= 0) || (rightIndex >= 0));
        if (isNaN(this.video.duration)) {
            this.leftPanel.status.innerHTML = "none";
            this.rightPanel.status.innerHTML = "none";
            return;
        }

        // deal with tied sliders
        if (this._tiedframes) {
            if (leftIndex < 0) {
                leftIndex = rightIndex - this.time2indx(this.rightPanel.timestamp) + this.time2indx(this.leftPanel.timestamp);
                // check we haven't gone past video boundary
                if ((leftIndex < 0) || (leftIndex > Math.floor(FPS * this.video.duration))) {
                    leftIndex = Math.floor(Math.min(Math.max(0, leftIndex), FPS * this.video.duration), 0);
                    rightIndex = leftIndex - this.time2indx(this.leftPanel.timestamp) + this.time2indx(this.rightPanel.timestamp);
                    this.rightPanel.slider.value = rightIndex;
                }
                this.leftPanel.slider.value = leftIndex;
            } else if (rightIndex < 0) {
                rightIndex = leftIndex - this.time2indx(this.leftPanel.timestamp) + this.time2indx(this.rightPanel.timestamp);
                // check we haven't gone past video boundary
                if ((rightIndex < 0) || (rightIndex > Math.floor(FPS * this.video.duration))) {
                    rightIndex = Math.floor(Math.min(Math.max(0, rightIndex), FPS * this.video.duration), 0);
                    leftIndex = rightIndex - this.time2indx(this.rightPanel.timestamp) + this.time2indx(this.leftPanel.timestamp);
                    this.leftPanel.slider.value = leftIndex;
                }
                this.rightPanel.slider.value = rightIndex;
            }
        }

        this.vidRequestQ = []
        if (leftIndex >= 0) {
            const index = Math.floor(Math.min(Math.max(0, leftIndex), FPS * this.video.duration), 0);
            const ts = this.indx2time(index);
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
            const ts = this.indx2time(index);
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
        if (!this.bFrameCacheComplete) {
            this.bFrameCacheComplete = true;
            for (var i = 0; i < this.video.duration; i++) {
                if (this.frameCache[i] == null) {
                    this.bFrameCacheComplete = false;
                    this.vidRequestQ.push({timestamp: i, who: ANUVidLib.NONE});
                }
            }

            if (this.bFrameCacheComplete) console.log("...finished caching frames")
        }

        // trigger first video request
        if (this.vidRequestQ.length > 0) {
            this.video.currentTime = this.vidRequestQ[0].timestamp;
        }
    }

    // Seek to a specific timestamp in the video. A negative number means don't update unless tied.
    seekToTime(leftTime, rightTime, bUpdateSliders) {
        var leftIndex = this.time2indx(leftTime);
        var rightIndex = this.time2indx(rightTime);
        this.leftPanel.slider.value = leftIndex;
        this.rightPanel.slider.value = rightIndex;
        return this.seekToIndex(leftIndex, rightIndex);
    }

    // Swap left and right panels. Same effect as seekToTime(this.rightPanel.timestamp, this.leftPanel.timestamp, true)
    // but faster since no video seek is required.
    swap() {
        //this.seekToTime(this.rightPanel.timestamp, this.leftPanel.timestamp, true);
        //return;

        var tmp = this.leftPanel.frame.src;
        this.leftPanel.frame.src = this.rightPanel.frame.src;
        this.rightPanel.frame.src = tmp;

        tmp = this.leftPanel.timestamp;
        this.leftPanel.timestamp = this.rightPanel.timestamp;
        this.rightPanel.timestamp = tmp;

        this.leftPanel.slider.value = this.time2indx(this.leftPanel.timestamp);
        this.rightPanel.slider.value = this.time2indx(this.rightPanel.timestamp);

        //this.redraw();
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

        this.redraw();
    }

    // Redraw frames and annotations. Parameter 'side' can be LEFT, RIGHT or BOTH.
    redraw(side = ANUVidLib.BOTH) {
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
        // draw frame
        var context = panel.canvas.getContext('2d');
        if ((panel.frame != null) && (panel.frame.width > 0) && (panel.frame.height > 0)) {
            context.drawImage(panel.frame, 0, 0, panel.canvas.width, panel.canvas.height);

            if (this.greyframes) {
                let imgData = context.getImageData(0, 0, context.canvas.width, context.canvas.height);
                let pixels = imgData.data;
                for (var i = 0; i < pixels.length; i += 4) {
                    let intensity = parseInt(0.299 * pixels[i] + 0.587 * pixels[i + 1] + 0.114 * pixels[i + 2]);
                    pixels[i] = intensity; pixels[i + 1] = intensity; pixels[i + 2] = intensity;
                }
                context.putImageData(imgData, 0, 0);
            }
        } else {
            context.clearRect(0, 0, panel.canvas.width, panel.canvas.height);
        }

        // draw objects
        if (this.objectList.length > 0) {
            let frameIndex = this.time2indx(panel.timestamp);
            for (var i = 0; i < this.objectList[frameIndex].length; i++) {
                this.objectList[frameIndex][i].draw(context, this.objectList[frameIndex][i] == this.activeObject);
            }
        }

        // draw border
        context.lineWidth = 7; context.strokeStyle = "#ffffff";
        roundedRect(context, 0, -2, panel.canvas.width, panel.canvas.height + 5, 9);
        context.stroke();
        context.lineWidth = 5; context.strokeStyle = "#000000";
        context.strokeRect(0, -2, panel.canvas.width, panel.canvas.height + 5);
        roundedRect(context, 0, -2, panel.canvas.width, panel.canvas.height + 5, 9);
        context.stroke();

        // update status
        if (panel.timestamp == null) {
            panel.status.innerHTML = "none";
        } else {
            panel.status.innerHTML = panel.timestamp.toFixed(2) + " / " + this.video.duration.toFixed(2) + "s [" +
                this.video.videoWidth + "-by-" + this.video.videoHeight + "]";
        }
    }

    // Get active object at position (x, y) on given panel.
    findActiveObject(x, y, panel) {
        const frameIndex = this.time2indx(panel.timestamp);
        for (var i = this.objectList[frameIndex].length - 1; i >= 0; i--) {
            if (this.objectList[frameIndex][i].nearBoundary(x, y, panel.canvas.width, panel.canvas.height)) {
                return this.objectList[frameIndex][i];
            }
        }

        return null;
    }

    // Process mouse movement over a panel.
    mousemove(event, side) {
        console.assert((side == ANUVidLib.LEFT) || (side == ANUVidLib.RIGHT), "invalid side");
        console.log("mouse moving in " + ((side == ANUVidLib.LEFT) ? "left" : "right"));

        // get current panel
        const panel = (side == ANUVidLib.LEFT) ? this.leftPanel : this.rightPanel;

        // handle dragging
        if (this.dragContext.mode == DragContext.MOVING) {
            this.activeObject.x += event.movementX / panel.canvas.width;
            this.activeObject.y += event.movementY / panel.canvas.height;
            this.paint(panel);
            if (this.leftPanel.timestamp == this.rightPanel.timestamp) {
                this.paint((side == ANUVidLib.RIGHT) ? this.leftPanel : this.rightPanel);
            }
            return;
        }

        if (this.dragContext.mode == DragContext.SIZING) {
            const x = this.dragContext.anchor.u / panel.canvas.width;
            const y = this.dragContext.anchor.v / panel.canvas.height;
            const w = event.movementX / panel.canvas.width + ((x > this.activeObject.x) ? -this.activeObject.width : this.activeObject.width);
            const h = event.movementY / panel.canvas.height + ((y > this.activeObject.y) ? -this.activeObject.height : this.activeObject.height);
            this.activeObject.resize(x, y, w, h);
            this.paint(panel);
            if (this.leftPanel.timestamp == this.rightPanel.timestamp) {
                this.paint((side == ANUVidLib.RIGHT) ? this.leftPanel : this.rightPanel);
            }
            return;
        }

        // search for an active object
        const lastActiveObject = this.activeObject;
        this.activeObject = this.findActiveObject(event.offsetX, event.offsetY, panel);

        // repaint if the active object changed
        if (this.activeObject != lastActiveObject) {
            this.paint(panel);
        }
    }

    // Process mouse leaving a panel.
    mouseout(event, side) {
        this.dragContext.mode = DragContext.NONE;
        if (this.activeObject != null) {
            this.activeObject = null;
            this.paint((side == ANUVidLib.LEFT) ? this.leftPanel : this.rightPanel);
            if (this.leftPanel.timestamp == this.rightPanel.timestamp) {
                this.paint((side == ANUVidLib.RIGHT) ? this.leftPanel : this.rightPanel);
            }
        }
    }

    // Process mouse button press inside panel.
    mousedown(event, side) {
        const panel = (side == ANUVidLib.LEFT) ? this.leftPanel : this.rightPanel;
        if (this.activeObject != null) {
            this.dragContext.anchor = this.activeObject.oppositeAnchor(event.offsetX, event.offsetY, panel.canvas.width, panel.canvas.height);
            if (this.dragContext.anchor == null) {
                this.dragContext.mode = DragContext.MOVING;
            } else {
                this.dragContext.mode = DragContext.SIZING;
            }
            this.dragContext.startX = event.offsetX;
            this.dragContext.startY = event.offsetY;
        }
    }

    // Process mouse button press inside panel.
    mouseup(event, side) {
        this.dragContext.mode = DragContext.NONE;

        if (this.activeObject != null) {
            this.activeObject = null;
            this.paint((side == ANUVidLib.LEFT) ? this.leftPanel : this.rightPanel);
            if (this.leftPanel.timestamp == this.rightPanel.timestamp) {
                this.paint((side == ANUVidLib.RIGHT) ? this.leftPanel : this.rightPanel);
            }
        }
    }
}

/*
** Annotation Utility Functions
*/

function newclip() {
    var table = document.getElementById(VIDSEGTABLENAME);
    var row = table.insertRow(-1);
    row.insertCell(0).innerHTML = v.leftPanel.timestamp;
    row.insertCell(1).innerHTML = v.rightPanel.timestamp;
    var input = document.createElement("input");
    input.type = "text"; input.classList.add("segdesc");
    parent = row.insertCell(2);
    parent.appendChild(input);
    var cell = row.insertCell(3);
    cell.innerHTML = "<button title='delete' onclick='delclip(this.parentElement.parentElement);'>&#x2718;</button>";
    cell.innerHTML += " <button title='move up' onclick='todo();'>&#x1F819;</button>";
    cell.innerHTML += " <button title='move down' onclick='todo();'>&#x1F81B;</button>";
    cell.innerHTML += " <button title='goto' onclick='v.seekToTime(" +
        v.leftPanel.timestamp + ", " + v.rightPanel.timestamp + ", true);'>&#x270E;</button>";
    cell.style.textAlign = "right";
    input.onkeypress = function(event) { defocusOnEnter(event, document.getElementById(LEFTSLIDERNAME)); }
    input.focus();
}

function delclip(row) {
    var table = document.getElementById(VIDSEGTABLENAME);
    table.deleteRow(row.rowIndex);
}

function clearclips() {
    var table = document.getElementById(VIDSEGTABLENAME);
    for (var i = table.rows.length - 1; i > 0; i--) {
        table.deleteRow(i);
    }
}