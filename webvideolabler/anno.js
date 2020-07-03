/*******************************************************************************
** ANUVIDLIB: A Javascript library for browser-based video annotation.
** Copyright (C) 2020, Stephen Gould <stephen.gould@anu.edu.au>
**
** Classes representing annotation types.
*******************************************************************************/

/* Frame Objects -------------------------------------------------------------*/

// Object bounding box representation. Coordinates between 0 and 1, where 1
// is the width or height of the image frame.
class ObjectBox {
    constructor(x, y, w, h, labelId = null, instanceId = null, colour = null, score = 1.0) {
        if (w < 0) {
            this.x = x + w;
            this.width = -w;
        } else {
            this.x = x;
            this.width = w;
        }

        if (h < 0) {
            this.y = y + h;
            this.height = -h;
        } else {
            this.y = y;
            this.height = h;
        }

        this.labelId = labelId;
        this.instanceId = instanceId;
        this.colour = colour;
        this.score = score;

        console.log(colour);
    }

    // Draw the object onto a canvas (context). Highlight to provide visual indication of selected.
    draw(ctx, highlight = false) {
        // TODO: something with highlight

        const u = this.x * ctx.canvas.width;
        const v = this.y * ctx.canvas.height;
        const w = this.width * ctx.canvas.width;
        const h = this.height * ctx.canvas.height;

        ctx.lineWidth = 3; ctx.strokeStyle = "#000000";
        ctx.strokeRect(u, v, w, h);
        ctx.lineWidth = 1;
        ctx.strokeStyle = (this.colour != null) ? this.colour : "#00ff00";
        ctx.strokeRect(u, v, w, h);

        const handle = 8;
        if ((w > handle) && (h > handle)) {
            ctx.beginPath();
            ctx.moveTo(u, v + handle); ctx.lineTo(u, v); ctx.lineTo(u + handle, v);
            ctx.moveTo(u, v + h - handle); ctx.lineTo(u, v + h); ctx.lineTo(u + handle, v + h);
            ctx.moveTo(u + w, v + handle); ctx.lineTo(u + w, v); ctx.lineTo(u + w - handle, v);
            ctx.moveTo(u + w, v + h - handle); ctx.lineTo(u + w, v + h); ctx.lineTo(u + w - handle, v + h);
            ctx.lineWidth = 5; ctx.strokeStyle = "#000000";
            ctx.stroke();
            ctx.lineWidth = 3; ctx.strokeStyle = (this.colour != null) ? this.colour : "#00ff00";
            ctx.stroke();
        }
    }

    // Check if mouse is positioned near an anchor point, i.e., box corner.
    nearAnchor(x, y) {
        // TODO
        return false;
    }
}

/* Video Objects -------------------------------------------------------------*/

class VidSegment {
    constructor(start, end, description) {
        this.start = start;
        this.end = end;
        this.description = description;
    }
}