/*******************************************************************************
** imagecrf.js
** Copyright (C) 2015, Stephen Gould <stephen.gould@anu.edu.au>
**
** Requires maxflow.js
*******************************************************************************/

function imageCRFPixelSqrDiff(imageData, x1, y1, x2, y2) {
    var i1 = 4 * (y1 * imageData.width + x1);
    var i2 = 4 * (y2 * imageData.width + x2);
    var d = 0.0;
    for (var c = 0; c < 3; c++) {
        d += (imageData.data[i1 + c] - imageData.data[i2 + c]) * (imageData.data[i1 + c] - imageData.data[i2 + c]);
    }
    return d;
}

function imageCRFContrast(imageData) {
    var contrast = {};

    // averaging
    var beta = 0.0;
    var count = 0;

    // north
    contrast.north = [];
    for (var y = 1; y < imageData.height; y++) {
        var column = [];
        for (var x = 0; x < imageData.width; x++) {
            column[x] = imageCRFPixelSqrDiff(imageData, x, y, x, y - 1);
            beta += column[x];
            count += 1;
        }
        contrast.north[y] = column;
    }

    // west
    contrast.west = [];
    for (var y = 0; y < imageData.height; y++) {
        var column = [];
        column[0] = Number.NaN;
        for (var x = 1; x < imageData.width; x++) {
            column[x] = imageCRFPixelSqrDiff(imageData, x, y, x - 1, y);
            beta += column[x];
            count += 1;
        }
        contrast.west[y] = column;
    }

    // TODO: north-west
    // TODO: north-east

    // exponentiate normalized contrasts
    beta = -1.0 * count / beta;
    for (var key in contrast) {
        for (var y = 0; y < contrast[key].length; y++) {
            if (typeof(contrast[key][y]) == "undefined") continue;
            for (var x = 0; x < contrast[key][y].length; x++) {
                if (contrast[key][y][x] != Number.NaN) {
                    contrast[key][y][x] = Math.exp(beta * contrast[key][y][x]);
                }
            }
        }
    }

    return contrast;
}

// Label an image with unary and pairwise terms.
function imageCRFLabel(imageData, unary, lambda)
{
    var contrast = imageCRFContrast(imageData);

    // constract maxflow graph
    var g = maxFlowInit();
    maxFlowAddNodes(g, imageData.width * imageData.height);
    
    // add unary terms
    for (var y = 0; y < imageData.height; y++) {
        for (var x = 0; x < imageData.width; x++) {
            var u = y * imageData.width + x;
            maxFlowAddSourceEdge(g, u, unary[y][x]);
        }
    }

    // add pairwise terms
    for (var y = 1; y < imageData.height; y++) {
        for (var x = 0; x < imageData.width; x++) {
            var u = (y - 1) * imageData.width + x;
            var v = y * imageData.width + x;
            maxFlowAddEdge(g, u, v, lambda * contrast.north[y][x]);
            maxFlowAddEdge(g, v, u, lambda * contrast.north[y][x]);
        }
    }

    for (var y = 0; y < imageData.height; y++) {
        for (var x = 1; x < imageData.width; x++) {
            var u = y * imageData.width + x;
            maxFlowAddEdge(g, u, u - 1, lambda * contrast.west[y][x]);
            maxFlowAddEdge(g, u - 1, u, lambda * contrast.west[y][x]);
        }
    }

    // find mincut
    var f = maxFlowBK(g);

    // generate labels
    var labels = [];
    for (var y = 0; y < imageData.height; y++) {
        var column = [];
        for (var x = 0; x < imageData.width; x++) {
            var u = y * imageData.width + x;            
            column[x] = (g.cut[u] == MAX_FLOW_SOURCE) ? 1 : 0;
        }
        labels[y] = column;
    }

    return labels;
}
