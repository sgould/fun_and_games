/*******************************************************************************
**  maxflow.js
** Copyright (C) 2015, Stephen Gould <stephen.gould@anu.edu.au>
*******************************************************************************/

function maxFlowInit()
{
    var g = {};

    g.sourceEdges = [];   // edges leaving the source node
    g.targetEdges = [];   // edges entering the target node
    g.nodes = [];         // nodes and their outgoing internal edges
    g.flowValue = 0;      // current flow value

    g.cut = [];           // S-set or T-set for each node

    return g;
}

function maxFlowNumNodes(g)
{
    return g.nodes.length;
}

function maxFlowAddNodes(g, n) {
    for (var i = 0; i < n; i++) {
        g.nodes.push([]);
        g.sourceEdges.push(0.0);
        g.targetEdges.push(0.0);
        g.cut.push(-1);
    }
}

function maxFlowAddConstant(g, c)
{
    g.flowValue += c;
}

function maxFlowAddSourceEdge(g, u, c)
{
    g.sourceEdges[u] += c;
}

function maxFlowAddTargetEdge(g, u, c)
{
    g.targetEdges[u] += c;
}

// Add an edge to the graph from u to v with (positive) capacity c.
function maxFlowAddEdge(g, u, v, c)
{
    if (u == v) return;

    var indx = maxFlowFindEdge(g, u, v);
    if (indx < 0) {
        g.nodes[u].push({node: v, w: c,   rindx: g.nodes[v].length});
        g.nodes[v].push({node: u, w: 0.0, rindx: g.nodes[u].length - 1});
    } else {
        g.nodes[u][indx].w += c;
    }
}

// Returns the index of the neighbour of u in g.
function maxFlowFindEdge(g, u, v)
{
    for (var i = 0; i < g.nodes[u].length; i++) {
        if (g.nodes[u][i].node == v) {
            return i;
        }
    }

    return -1;
}

function maxFlowPreAugment(g)
{
    for (var u = 0; u < g.nodes.length; u++) {
        // augment s-u-t paths
        if ((g.sourceEdges[u] > 0.0) && (g.targetEdges[u] > 0.0)) {
            var c = Math.min(g.sourceEdges[u], g.targetEdges[u]);
            g.flowValue += c;
            g.sourceEdges[u] -= c;
            g.targetEdges[u] -= c;
        }

        if (g.sourceEdges[u] == 0.0) continue;

        // augment s-u-v-t paths
        for (var i = 0; i < g.nodes[u].length; i++) {
            var v = g.nodes[u][i].node;
            if ((g.nodes[u][i].w == 0.0) || (g.targetEdges[v] == 0.0)) continue;

            var w = Math.min(g.nodes[u][i].w, Math.min(g.sourceEdges[u], g.targetEdges[v]));
            g.sourceEdges[u] -= w;
            g.targetEdges[u] -= w;
            g.nodes[u][i].w -= w;
            g.nodes[v][g.nodes[u][i].rindx] += w;
            g.flowValue += w;

            if (g.sourceEdges[u] == 0.0) break;
        }
    }
}

function maxFlowPrint(g)
{
    var str = "";
    for (var v = 0; v < g.sourceEdges.length; v++) {
        if (g.sourceEdges[v] > 0.0) {
            str += "s --> " + v + " : " + g.sourceEdges[v] + "\n";
        }
    }

    for (var u = 0; u < g.nodes.length; u++) {
        for (var i = 0; i < g.nodes[u].length; i++) {
            if (g.nodes[u][i].w > 0.0) {
                str += u + " --> " + g.nodes[u][i].node + " : " + g.nodes[u][i].w + "\n";
            }
        }
    }

    for (var u = 0; u < g.targetEdges.length; u++) {
        if (g.targetEdges[u] > 0.0) {
            str += u + " --> t : " + g.targetEdges[u] + "\n";
        }
    }

    return str;
}

function maxFlowEdmondsKarp(g)
{
    // pre-augment
    maxFlowPreAugment(g);

    while (true) {
        // find augmenting path
        var frontier = [];
        var backtrack = [];
        for (var u = 0; u < g.nodes.length; u++) {
            if (g.sourceEdges[u] > 0.0) {
                frontier.push(u);
                backtrack.push(-1);
            } else {
                backtrack.push(-2);
            }
        }

        var u = -1;
        while (frontier.length > 0) {
            u = frontier.shift(); // pop and return front
            if (g.targetEdges[u] > 0.0) {
                break;
            }
            for (var i = 0; i < g.nodes[u].length; i++) {
                if ((g.nodes[u][i].w > 0.0) && (backtrack[g.nodes[u][i].node] == -2)) {
                    frontier.push(g.nodes[u][i].node);
                    backtrack[g.nodes[u][i].node] = u;
                }
            }

            u = -1;
        }

        if (u == -1) break;

        // backtrack
        var path = [];
        var c = g.targetEdges[u];
        while (backtrack[u] != -1) {
            var v = u;
            u = backtrack[v];
            var e = maxFlowFindEdge(g, u, v);
            c = Math.min(c, g.nodes[u][e].w);
            path.push(e);
        }
        c = Math.min(c, g.sourceEdges[u]);

        g.sourceEdges[u] -= c;
        for (var i = path.length - 1; i >= 0; i--) {
            var v = g.nodes[u][path[i]].node;
            g.nodes[u][path[i]].w -= c;
            g.nodes[v][g.nodes[u][path[i]].rindx].w += c;
            u = v;
        }
        g.targetEdges[u] -= c;

        g.flowValue += c;
    }

    // fill cut variable with 1 for S-set and 0 for T-set
    for (var u = 0; u < g.cut.length; u++) {
        g.cut[u] = 0;
    }

    var frontier = [];
    for (var u = 0; u < g.nodes.length; u++) {
        if (g.sourceEdges[u] > 0.0) {
            frontier.push(u);
            g.cut[u] = 1;
        }

        while (frontier.length > 0) {
            var u = frontier.shift();
            for (var i = 0; i < g.nodes[u].length; i++) {
                var v = g.nodes[u][i].node;
                if ((g.nodes[u][i].w > 0.0) && (g.cut[v] != 1)) {
                    frontier.push(v);
                    g.cut[v] = 1;
                }
            }
        }
    }
}
