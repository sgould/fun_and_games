/*******************************************************************************
**  maxflow.js
** Copyright (C) 2015, Stephen Gould <stephen.gould@anu.edu.au>
*******************************************************************************/

const MAX_FLOW_FREE = -2;
const MAX_FLOW_TERMINAL = -1;
const MAX_FLOW_TARGET = 0;
const MAX_FLOW_SOURCE = 1;

function maxFlowAssert(b, msg)
{
    if (b) throw new Error(msg);
}

function maxFlowInit()
{
    var g = {};

    g.sourceEdges = [];   // edges leaving the source node
    g.targetEdges = [];   // edges entering the target node
    g.nodes = [];         // nodes and their outgoing internal edges (node, w, rindx)
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
    if ((u >= g.nodes.length) || (v >= g.nodes.length)) {
        abort();
    }

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
            var ri = g.nodes[u][i].rindx;
            if ((g.nodes[u][i].w == 0.0) || (g.targetEdges[v] == 0.0)) continue;

            var w = Math.min(g.nodes[u][i].w, Math.min(g.sourceEdges[u], g.targetEdges[v]));
            g.sourceEdges[u] -= w;
            g.targetEdges[v] -= w;
            g.nodes[u][i].w -= w;
            g.nodes[v][ri].w += w;
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
                backtrack.push(MAX_FLOW_TERMINAL);
            } else {
                backtrack.push(MAX_FLOW_FREE);
            }
        }

        var u = MAX_FLOW_TERMINAL;
        while (frontier.length > 0) {
            u = frontier.shift(); // pop and return front
            if (g.targetEdges[u] > 0.0) {
                break;
            }
            for (var i = 0; i < g.nodes[u].length; i++) {
                if ((g.nodes[u][i].w > 0.0) && (backtrack[g.nodes[u][i].node] == MAX_FLOW_FREE)) {
                    frontier.push(g.nodes[u][i].node);
                    backtrack[g.nodes[u][i].node] = u;
                }
            }

            u = MAX_FLOW_TERMINAL;
        }

        if (u == MAX_FLOW_TERMINAL) break;

        // backtrack
        var path = [];
        var c = g.targetEdges[u];
        while (backtrack[u] != MAX_FLOW_TERMINAL) {
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
            var ri = g.nodes[u][path[i]].rindx;
            g.nodes[u][path[i]].w -= c;
            g.nodes[v][ri].w += c;
            u = v;
        }
        g.targetEdges[u] -= c;

        g.flowValue += c;
    }

    // fill cut variable with 1 for S-set and 0 for T-set
    for (var u = 0; u < g.cut.length; u++) {
        g.cut[u] = MAX_FLOW_TARGET;
    }

    var frontier = [];
    for (var u = 0; u < g.nodes.length; u++) {
        if (g.sourceEdges[u] > 0.0) {
            frontier.push(u);
            g.cut[u] = MAX_FLOW_SOURCE;
        }

        while (frontier.length > 0) {
            var u = frontier.shift();
            for (var i = 0; i < g.nodes[u].length; i++) {
                var v = g.nodes[u][i].node;
                if ((g.nodes[u][i].w > 0.0) && (g.cut[v] != MAX_FLOW_SOURCE)) {
                    frontier.push(v);
                    g.cut[v] = MAX_FLOW_SOURCE;
                }
            }
        }
    }

    return g.flowValue;
}

function maxFlowBK(g)
{
    // pre-augment paths
    maxFlowPreAugment(g);

    // initialize search trees
    var parents = [];
    var active = [];
    for (var u = 0; u < g.nodes.length; u++) {
        if (g.sourceEdges[u] > 0.0) {
            g.cut[u] = MAX_FLOW_SOURCE;
            parents.push(MAX_FLOW_TERMINAL);
            active.push(u);
        } else if (g.targetEdges[u] > 0.0) {
            g.cut[u] = MAX_FLOW_TARGET;
            parents.push(MAX_FLOW_TERMINAL);
            active.push(u);
        } else {
            parents.push(MAX_FLOW_FREE);
            g.cut[u] = MAX_FLOW_FREE;
        }
    }

    // find augmenting paths
    while (active.length > 0) {
        // expand trees
        var u = active[0];
        var path = [];
        if (g.cut[u] == MAX_FLOW_SOURCE) {
            for (var i = 0; i < g.nodes[u].length; i++) {
                var v = g.nodes[u][i].node;
                if (g.nodes[u][i].w > 0.0) {
                    if (g.cut[v] == MAX_FLOW_FREE) {
                        g.cut[v] = MAX_FLOW_SOURCE;
                        parents[v] = g.nodes[u][i].rindx;
                        active.push(v);
                    } else if (g.cut[v] == MAX_FLOW_TARGET) {
                        // found augmenting path (node, neighbour index)
                        path = [u, i];
                        break;
                    }
                }
            }
        } else {
            for (var i = 0; i < g.nodes[u].length; i++) {
                var v = g.nodes[u][i].node;
                var ri = g.nodes[u][i].rindx;
                if (g.nodes[v][ri].w > 0.0) {
                    if (g.cut[v] == MAX_FLOW_FREE) {
                        g.cut[v] = MAX_FLOW_TARGET;
                        parents[v] = ri;
                        active.push(v);
                    } else if (g.cut[v] == MAX_FLOW_SOURCE) {
                        // found augmenting path (node, neighbour index)
                        path = [v, ri];
                        break;
                    }
                }
            }
        }

        if (path.length == 0) { active.shift(); continue; }

        // augment path
        //console.log("Found augmenting path: " + path[0] + ", " + g.nodes[path[0]][path[1]].node);
        var c = g.nodes[path[0]][path[1]].w;
        //console.log("edge(" + path[0] + " --> " + g.nodes[path[0]][path[1]].node + ") = " + c);
        // backtrack
        u = path[0];
        while (parents[u] != MAX_FLOW_TERMINAL) {
            var v = g.nodes[u][parents[u]].node;
            var ri = g.nodes[u][parents[u]].rindx;
            //console.log("edge(" + v + " --> " + u + ") = " + g.nodes[v][ri].w);
            c = Math.min(c, g.nodes[v][ri].w);
            u = v;
        }
        //console.log("edge(s --> " + u + ") = " + g.sourceEdges[u]);
        c = Math.min(c, g.sourceEdges[u]);

        // forward track
        u = g.nodes[path[0]][path[1]].node;
        while (parents[u] != MAX_FLOW_TERMINAL) {
            var v = g.nodes[u][parents[u]].node;
            //console.log("edge(" + u + " --> " + v + ") = " + g.nodes[u][parents[u]].w);
            c = Math.min(c, g.nodes[u][parents[u]].w);
            u = v;
        }
        //console.log("edge(" + u + " --> t) = " + g.targetEdges[u]);
        c = Math.min(c, g.targetEdges[u]);

        //console.log("residual capacity is " + c);
        maxFlowAssert(c == 0.0, "zero capacity augmenting path");

        orphans = [];
        u = path[0];
        v = g.nodes[u][path[1]].node;
        g.nodes[u][path[1]].w -= c;
        g.nodes[v][g.nodes[u][path[1]].rindx].w += c;
        while (parents[u] != MAX_FLOW_TERMINAL) {
            var v = g.nodes[u][parents[u]].node;
            var ri = g.nodes[u][parents[u]].rindx;
            g.nodes[v][ri].w -= c;
            g.nodes[u][parents[u]].w += c;
            if (g.nodes[v][ri].w == 0.0) {
                orphans.push(u);
            }
            u = v;
        }
        g.sourceEdges[u] -= c;
        if (g.sourceEdges[u] == 0.0) {
            orphans.push(u);
        }
        u = g.nodes[path[0]][path[1]].node;
        while (parents[u] != MAX_FLOW_TERMINAL) {
            var v = g.nodes[u][parents[u]].node;
            var ri = g.nodes[u][parents[u]].rindx;
            g.nodes[u][parents[u]].w -= c;
            g.nodes[v][ri].w += c;
            if (g.nodes[u][parents[u]].w == 0.0) {
                orphans.push(u);
            }
            u = v;
        }
        g.targetEdges[u] -= c;
        if (g.targetEdges[u] == 0.0) {
            orphans.push(u);
        }

        g.flowValue += c;

        // adopt orphans
        //console.log("orphans: " + orphans);

// BEGIN DEBUGGING
        if (false && (orphans.length > 0)) {
            parents = [];
            active = [];
            for (var u = 0; u < g.nodes.length; u++) {
                if (g.sourceEdges[u] > 0.0) {
                    g.cut[u] = MAX_FLOW_SOURCE;
                    parents.push(MAX_FLOW_TERMINAL);
                    active.push(u);
                } else if (g.targetEdges[u] > 0.0) {
                    g.cut[u] = MAX_FLOW_TARGET;
                    parents.push(MAX_FLOW_TERMINAL);
                    active.push(u);
                } else {
                    parents.push(MAX_FLOW_FREE);
                    g.cut[u] = MAX_FLOW_FREE;
                }
            }

            orphans = [];
        }
/// END DEBUGGING
        
        for (var i = 0; i < orphans.length; i++) {
            parents[orphans[i]] = MAX_FLOW_TERMINAL;
        }

        while (orphans.length > 0) {
            var u = orphans.pop();
            var treeLabel = g.cut[u];

            var bFreeOrphan = true;
            for (var i = 0; i < g.nodes[u].length; i++) {
                // check if different tree or no capacity
                var v = g.nodes[u][i].node;
                var ri = g.nodes[u][i].rindx;
                //console.log("...orphan " + u + " is checking adoption by " + v + " (" + treeLabel + ")");
                if (g.cut[v] != treeLabel) continue;
                if ((treeLabel == MAX_FLOW_SOURCE) && (g.nodes[v][ri].w == 0.0)) continue;
                if ((treeLabel == MAX_FLOW_TARGET) && (g.nodes[u][i].w == 0.0)) continue;

                // check that u is not an ancestor of v
                while ((v != u) && (parents[v] != MAX_FLOW_TERMINAL)) {
                    //console.log("...parent of " + v + " is " + g.nodes[v][parents[v]].node);
                    v = g.nodes[v][parents[v]].node;                    
                }
                //console.log("...parent of " + v + " is " + (treeLabel == MAX_FLOW_TARGET ? "t" : "s"));
                if (v == u) continue;

                // add as parent
                //console.log("...orphan " + u + " adopted by " + g.nodes[u][i].node + " (" + treeLabel + ")");
                parents[u] = i;
                bFreeOrphan = false;
                break;
            }

            if (bFreeOrphan) {
                //console.log("...freeing orphan " + u);
                for (var i = 0; i < g.nodes[u].length; i++) {
                    var v = g.nodes[u][i].node;
                    if ((g.cut[v] == treeLabel) && (parents[v] == g.nodes[u][i].rindx)) {
                        parents[v] = MAX_FLOW_TERMINAL;
                        orphans.push(v);
                        if (active.indexOf(v) == -1) active.push(v);
                    }
                }

                // mark inactive and free
                var indx = active.indexOf(u);
                if (indx != -1) active.splice(indx, 1);
                g.cut[u] = MAX_FLOW_FREE;
            }
        }
    }

    return g.flowValue;
}
