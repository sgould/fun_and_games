#!/usr/bin/env python3
# -----------------------------------------------------------------------
# BLOKUS Copyright 2015, Stephen Gould <stephen.gould@anu.edu.au>
# -----------------------------------------------------------------------
# Code for playing a game of Blokus, a game developed by Bernard
# Tavitian and now owned by Mattel.
# -----------------------------------------------------------------------

__author__ = "Stephen Gould"

from collections import deque
from copy import deepcopy
import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import RegularPolygon

class Piece(object):
    """Encapsulates a piece."""

    blocks = ()      # coordinates of the blocks
    rotations = 0    # number of unique orientations
    symmetry = False # mirror symmetry

    def __init__(self, blocks, rotations=4, symmetry=False):
        assert blocks[0] == (0, 0)
        self.blocks = blocks
        self.rotations = rotations
        self.symmetry = symmetry

    def __str__(self):
        return str(self.blocks)

    def size(self):
        """Return the number of blocks in this piece."""
        return len(self.blocks)

    def rotate(self):
        """Rotate a piece by 90 degree clockwise."""
        self.blocks = tuple([(y, -x) for (x, y) in list(self.blocks)])

    def flip(self):
        """Flip a piece about the vertical axis."""
        self.blocks = tuple([(x, -y) for (x, y) in list(self.blocks)])

    def generator(self):
        """Generator for this piece."""
        r = 0
        while r < self.rotations:
            yield self.blocks
            self.rotate()
            r += 1

        if not self.symmetry:
            self.flip()
            while r > 0:
                yield self.blocks
                self.rotate()
                r -= 1

class Player(object):
    """Encapsulates a player agent."""

    def __init__(self, id):
        assert 1 <= id <= 4
        self.id = id
        self.pieces = []
        self.add_piece(((0, 0), ), 1, True)                                 # 1-by-1
        self.add_piece(((0, 0), (1, 0)), 2, True)                           # 1-by-2
        self.add_piece(((0, 0), (1, 0), (1, 1)), 4, True)                   # 3-corner
        self.add_piece(((0, 0), (1, 0), (2, 0)), 2, True)                   # 1-by-3
        self.add_piece(((0, 0), (1, 0), (1, 1), (0, 1)), 1, True)           # 2-by-2
        self.add_piece(((0, 0), (1, 0), (2, 0), (1, 1)), 4, True)           # 4-tee
        self.add_piece(((0, 0), (1, 0), (2, 0), (3, 0)), 2, True)           # 1-by-4
        self.add_piece(((0, 0), (1, 0), (2, 0), (2, 1)))                    # 4-ell
        self.add_piece(((0, 0), (1, 0), (1, 1), (2, 1)), 2)                 # 4-ess
        self.add_piece(((0, 0), (1, 0), (2, 0), (3, 0), (3, 1)))            # 5-ell
        self.add_piece(((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)), 4, True)   # 5-corner
        self.add_piece(((0, 0), (1, 0), (1, 1), (2, 1), (3, 1)))            # 5-ess
        self.add_piece(((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)), 2)         # 5-ess'
        self.add_piece(((0, 0), (1, 0), (2, 0), (3, 0), (4, 0)), 2, True)   # 1-by-5
        self.add_piece(((0, 0), (0, 1), (1, 1), (1, 0), (0, 2)))            # 5
        self.add_piece(((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)), 4, True)   # 5
        self.add_piece(((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)), 4, True)   # 5-cee
        self.add_piece(((0, 0), (1, 0), (1, 1), (1, 2), (2, 1)))            # 5
        self.add_piece(((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)), 1, True) # 5-plus
        self.add_piece(((0, 0), (1, 0), (2, 0), (3, 0), (1, 1)))            # 5
        self.last_played = None

    def add_piece(self, blocks, rotations=4, symmetry=False):
        """Add a piece to this player's set of pieces."""
        self.pieces.append(Piece(blocks, rotations, symmetry))

    def remove_piece(self, indx):
        """Remove a piece from this player's set of piece."""
        self.last_played = self.pieces[indx]
        del self.pieces[indx]

    def score(self):
        """Computes the score for this player."""
        if not self.pieces:
            return 20 if self.last_played.size() == 1 else 15
        return -1 * sum([p.size() for p in self.pieces])


class Board(object):
    """Encapsulates a game board."""
    ROWS, COLS = 20, 20

    def __init__(self, state = None):
        if (state is not None):
            assert state.shape == (self.ROWS, self.COLS)
            self.board = np.copy(state)
        else:
            self.board = np.zeros((self.ROWS, self.COLS), dtype=np.byte)
        self.cant_have_any_map = [None for p in range(4)]
        self.must_have_one_map = [None for p in range(4)]

    def copy(self):
        """Creates a copy of the board."""
        b = Board(self.board)
        b.cant_have_any_map = deepcopy(self.cant_have_any_map)
        b.must_have_one_map = deepcopy(self.must_have_one_map)
        return b

    def get_free_cells(self):
        """Returns list of free cells."""
        cells = []
        for row in range(self.ROWS):
            for col in range(self.COLS):
                if self.board[row, col] == 0:
                    cells.append((col, row))
        return cells

    def get_validity_map(self, player):
        """Returns a map of valid cell locations for a given player. Used internally
        by is_legal_placement."""

        cant_have_any_map  = np.zeros((self.ROWS, self.COLS), dtype=np.byte)
        must_have_one_map  = np.zeros((self.ROWS, self.COLS), dtype=np.byte)
        for row in range(self.ROWS):
            for col in range(self.COLS):
                if self.board[row, col] != 0:
                    cant_have_any_map[row, col] = 1
                else:
                    if (row > 0) and (self.board[row - 1, col] == player):
                        cant_have_any_map[row, col] = 1
                    if (row + 1 < self.ROWS) and (self.board[row + 1, col] == player):
                        cant_have_any_map[row, col] = 1
                    if (col > 0) and (self.board[row, col - 1] == player):
                        cant_have_any_map[row, col] = 1
                    if (col + 1 < self.COLS) and (self.board[row, col + 1] == player):
                        cant_have_any_map[row, col] = 1

                    if (row > 0) and (col > 0) and (self.board[row - 1, col - 1] == player):
                        must_have_one_map[row, col] = 1
                    if (row > 0) and (col + 1 < self.COLS) and (self.board[row - 1, col + 1] == player):
                        must_have_one_map[row, col] = 1
                    if (row + 1 < self.ROWS) and (col > 0) and (self.board[row + 1, col - 1] == player):
                        must_have_one_map[row, col] = 1
                    if (row + 1 < self.ROWS) and (col + 1 < self.COLS) and (self.board[row + 1, col + 1] == player):
                        must_have_one_map[row, col] = 1

        if self.board[0, 0] == 0:
            must_have_one_map[0, 0] = 1
        else:
            must_have_one_map[0, -1] = 1
            must_have_one_map[-1, 0] = 1
            must_have_one_map[-1, -1] = 1

        return cant_have_any_map, must_have_one_map


    def is_legal_placement(self, row, col, blocks, player):
        """Check that piece placement is legal."""
        assert 1 <= player <= 4

        if ((self.cant_have_any_map[player - 1] is None) or (self.must_have_one_map[player - 1] is None)):
            self.cant_have_any_map[player - 1], self.must_have_one_map[player - 1] = self.get_validity_map(player)

        legal = False
        for (x, y) in blocks:
            u, v = col + x, row + y
            if (0 <= u < self.COLS) and (0 <= v < self.ROWS):
                if self.cant_have_any_map[player - 1][v, u]:
                    return False
                if self.must_have_one_map[player - 1][v, u]:
                    legal = True
            else:
                return False

        return legal

    def place_piece(self, row, col, blocks, player):
        for (x, y) in blocks:
            self.board[row + y, col + x] = player

        self.cant_have_any_map[player - 1] = None
        self.must_have_one_map[player - 1] = None
        for p in range(4):
            if self.cant_have_any_map[p] is not None:
                for (x, y) in blocks:
                    self.cant_have_any_map[p][row + y, col + x] = 1

    def draw_board(self, squares):
        COLOURS = ["#afafaf", "#3f3fff", "#dfdf3f", "#df3f3f", "#1fdf1f"]
        for row in range(self.ROWS):
            for col in range(self.COLS):
                squares[row, col].set_facecolor(COLOURS[self.board[col, row]])


# TESTING
import sys

def expand_node(board, agent):
    children = deque()
    cells = board.get_free_cells()
    for i, p in enumerate(agent.pieces):
        print(["-", "/", "|", "\\"][i % 4], end="\r")
        for r in p.generator():
            for x, y in cells:
                if board.is_legal_placement(y, x, r, agent.id):
                    children.append((i, r, x, y))

    return children

def count_expand_node(board, agent):
    count = 0
    cells = board.get_free_cells()
    for i, p in enumerate(agent.pieces):
        print(["-", "/", "|", "\\"][i % 4], end="\r")
        for r in p.generator():
            for x, y in cells:
                if board.is_legal_placement(y, x, r, agent.id):
                    count += 1

    return count


initial_agents = [Player(p + 1) for p in range(4)]
initial_board = Board()

"""
frontier = deque()
frontier.append((0, initial_board.copy(), deepcopy(initial_agents)))
for n in range(1 + 56 + 56):
    player, board, agents = frontier.pop()

    moves = expand_node(board, agents[player])
    for i, r, x, y in moves:
        b = board.copy()
        b.place_piece(y, x, r, player + 1)
        a = deepcopy(agents)
        a[player].remove_piece(i)
        frontier.appendleft(((player + 1) % 4, b, a))

    print("player {}: {}".format(player + 1, len(frontier)))

sys.exit()
"""

"""
first_ply = expand_node(initial_board, initial_agents[0])
unique_moves = 0
for i, p in enumerate(agents[0].pieces):
    unique_moves += p.rotations * (1 if p.symmetry else 2)
print("{} moves in first ply from {} unique piece orientations".format(len(first_ply), unique_moves))
"""

for a in initial_agents:
    random.shuffle(a.pieces)

def ani(fnum, agents, board, squares):
    if (fnum == 0): return

    player = (fnum - 1) % len(agents)

    ply_moves = expand_node(board, agents[player])
    num_ply_moves = len(ply_moves)
    #num_ply_moves = count_expand_node(board, agents[player])
    print("{} moves for player {} in ply {}".format(num_ply_moves, player + 1, fnum))

    cells = board.get_free_cells()
    random.shuffle(cells)
    for i, p in enumerate(agents[player].pieces):
        for r in p.generator():
            for x, y in cells:
                if board.is_legal_placement(y, x, r, player + 1):
                    #print("...placing {} at ({}, {})".format(r, x, y))
                    board.place_piece(y, x, r, player + 1)
                    agents[player].remove_piece(i)
                    board.draw_board(squares)
                    plt.title("blue: {}, yellow: {}, red: {}, green: {}".format(
                        agents[0].score(), agents[1].score(), agents[2].score(), agents[3].score()))
                    return


# initialise graphics and start animation
plt.ioff()                # turn off interactive mode
fig = plt.figure()        # intialize the figure
ax = fig.add_axes((0.05, 0.05, 0.9, 0.9), aspect="equal", frameon=False,
    xlim=(-0.05, initial_board.COLS + 0.05), ylim=(-0.05, initial_board.ROWS + 0.05))
ax.xaxis.set_major_formatter(plt.NullFormatter())
ax.yaxis.set_major_formatter(plt.NullFormatter())
ax.xaxis.set_major_locator(plt.NullLocator())
ax.yaxis.set_major_locator(plt.NullLocator())
squares = np.array([[RegularPolygon((i + 0.5, j + 0.5), numVertices=4, radius=0.5 * np.sqrt(2),
    orientation=np.pi / 4, ec="#000000", fc="#ffffff") for j in range(initial_board.COLS)] for i in range(initial_board.ROWS)])
[ax.add_patch(sq) for sq in squares.flat]
animation.FuncAnimation(fig, ani, interval=100, repeat=False, fargs=(initial_agents, initial_board, squares), frames=84)
plt.show()

for p in initial_agents:
    print("Player {} scored {} ({} pieces remaining)".format(p.id, p.score(), len(p.pieces)))
