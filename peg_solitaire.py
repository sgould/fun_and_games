# 9x9 (45-HOLE) AND 7x7 (33-HOLE) PEG SOLITAIRE
# Stephen Gould
#
# Indexing (row,col) and classes:
#                                                               0 1 2 3 4 5 6 7 8
#                   (0,3) (0,4) (0,5)                        0:       C A C
#                   (1,3) (1,4) (1,5)                        1:       B D B
#                   (2,3) (2,4) (2,5)                        2:       C A C
# (3,0) (3,1) (3,2) (3,3) (3,4) (3,5) (3,6) (3,7) (3,8)      3: D B D B D B D B D
# (4,0) (4,1) (4,2) (4,3) (4,4) (4,5) (4,6) (4,7) (4,8)      4: A C A C A C A C A
# (5,0) (5,1) (5,2) (5,3) (5,4) (5,5) (5,6) (5,7) (5,8)      5: D B D B D B D B D
#                   (6,3) (6,4) (6,5)                        6:       C A C
#                   (7,3) (7,4) (7,5)                        7:       B D B
#                   (8,3) (8,4) (8,5)                        8:       C A C
#

import copy
import heapq
import time
import numpy as np


class GameState:
    """State of the board."""

    # hash index used for computing a hash of the game state
    hash_indx = np.array([
        [0,     0,      0,      65536,  16384,  65536,  0,      0,      0],
        [0,     0,      0,      2048,   512,    2048,   0,      0,      0],
        [0,     0,      0,      64,     16,     64,     0,      0,      0],
        [65536, 2048,   64,     4,      1,      4,      64,     2048,   65536],
        [16384, 512,    16,     1,      0,      1,      16,     512,    16384],
        [65536, 2048,   64,     4,      1,      4,      64,     2048,   65536],
        [0,     0,      0,      64,     16,     64,     0,      0,      0],
        [0,     0,      0,      2048,   512,    2048,   0,      0,      0],
        [0,     0,      0,      65536,  16384,  65536,  0,      0,      0]
    ], dtype=int)

    def __init__(self, init_state=None, goal_state=None, allow_symmetric=True):
        """
            init_state: 9-by-9 array with at least on empty location
            goal_state: 9-by-9 array with at least one peg location (and fewer pegs than init_state)
            allow_symmetric: allow (rotation and reflection) symmetry in solution

            Board states should be numpy arrays of type np.int8 with entries -1 for illegal location,
            0 for empty location, and 1 for peg location. The four 3-by-3 corners must be illegal.
        """

        if init_state is None:
            self.init_state = np.array([[-1 if ((i < 3) or (i > 5)) and ((j < 3) or (j > 5)) else 1 for j in range(9)] for i in range(9)], dtype=np.int8)
            self.init_state[4, 4] = 0
        else:
            self.init_state = init_state
        self.board = np.copy(self.init_state)

        if goal_state is None:
            self.goal = np.where(self.init_state == -1, -1, 1 - self.init_state)
        else:
            self.goal = goal_state

        # check valid init_state and goal_state
        assert self.board.shape == (9, 9) and self.goal.shape == (9, 9)
        mask = np.array([[1 if ((i < 3) or (i > 5)) and ((j < 3) or (j > 5)) else 0 for j in range(9)] for i in range(9)], dtype=np.int8)
        assert np.sum(np.where(self.board == -1, mask, 0)) == 36
        assert np.array_equal(self.board == -1, self.goal == -1)
        assert np.sum(self.board == 0) > 0
        assert np.sum(self.goal == 1) > 0

        self.count = np.count_nonzero(self.board == 1)
        self.init_count = self.count
        self.goal_count = np.count_nonzero(self.goal == 1)
        assert self.count >= self.goal_count

        self.allow_symmetric = allow_symmetric
        self.moves = np.empty((self.init_count - self.goal_count, 3), dtype=np.int8)

    @staticmethod
    def fill(value = 0, n = 45):
        """Returns a board filled with 'value' for n-hole game ('n' can be 33 or 45)."""
        assert (n == 33) or (n == 45)
        board = np.array([[-1 if ((i < 3) or (i > 5)) and ((j < 3) or (j > 5)) else value for j in range(9)] for i in range(9)], dtype=np.int8)
        if n == 33:
            board[0, :] = board[8, :] = board[:, 0] = board[:, 8] = -1
        return board

    @staticmethod
    def set(board, pegs):
        """Returns a new board with 'pegs' locations set to one."""
        board = copy.deepcopy(board)
        for p in pegs:
            board[p] = 1
        return board

    @staticmethod
    def clear(board, pegs):
        """Returns a new board with 'pegs' locations set to zero."""
        board = copy.deepcopy(board)
        for p in pegs:
            board[p] = 0
        return board

    @staticmethod
    def symmetric_cmp_eq(board, other):
        """Returns true if two boards are equal, taking into account symmetry."""
        if np.array_equal(board, other):
            return True

        other_transposed = np.transpose(other)
        if np.array_equal(board, other_transposed):
            return True

        b = np.fliplr(board)
        if np.array_equal(b, other):
            return True
        if np.array_equal(b, other_transposed):
            return True
        b = np.flipud(b)
        if np.array_equal(b, other):
            return True
        if np.array_equal(b, other_transposed):
            return True
        b = np.fliplr(b)
        if np.array_equal(b, other):
            return True
        if np.array_equal(b, other_transposed):
            return True

        return False

    @staticmethod
    def dir2str(d):
        """Convert direction to string."""
        if   d == 0: return "down"
        elif d == 1: return "right"
        elif d == 2: return "up"
        elif d == 3: return "left"
        return None

    @staticmethod
    def dir2delta(d):
        """Convert direction to di and dj."""
        if   d == 0: return 1, 0
        elif d == 1: return 0, 1
        elif d == 2: return -1, 0
        elif d == 3: return 0, -1
        return None

    @staticmethod
    def count_classes(board):
        """Returns the count of classes of pegs based on row a column odd/evenness. See Beasley, The Ins and Outs of
        Peg Solitaire, Chapter 2. Note that Beasley defines a 7x7 board."""

        pegs = np.mod(np.nonzero(board == 1), 2)
        nA = np.sum(np.logical_and(pegs[0] == 0, pegs[1] == 0))
        nB = np.sum(np.logical_and(pegs[0] == 1, pegs[1] == 1))
        nC = np.sum(np.logical_and(pegs[0] == 0, pegs[1] == 1))
        nD = np.sum(np.logical_and(pegs[0] == 1, pegs[1] == 0))

        return np.array([nA, nB, nC, nD], dtype=np.int8)

    @staticmethod
    def count_classes_by_zone(board):
        """Returns the count of classes (A, B, C and D) by zone (North, South, East, West, Centre)."""
        counts = np.zeros((4, 5), dtype=np.int8)

        # north
        counts[0, 0] = (1 if board[0, 4] == 1 else 0) + (1 if board[2, 4] == 1 else 0)
        counts[1, 0] = (1 if board[1, 3] == 1 else 0) + (1 if board[1, 5] == 1 else 0)
        counts[2, 0] = np.sum(board[0:3:2, 3:6:2] == 1)
        counts[3, 0] = 1 if board[1, 4] == 1 else 0

        # south
        counts[0, 1] = (1 if board[6, 4] == 1 else 0) + (1 if board[8, 4] == 1 else 0)
        counts[1, 1] = (1 if board[7, 3] == 1 else 0) + (1 if board[7, 5] == 1 else 0)
        counts[2, 1] = np.sum(board[6:9:2, 3:6:2] == 1)
        counts[3, 1] = 1 if board[7, 4] == 1 else 0

        # east
        counts[0, 2] = (1 if board[4, 6] == 1 else 0) + (1 if board[4, 8] == 1 else 0)
        counts[1, 2] = (1 if board[3, 7] == 1 else 0) + (1 if board[5, 7] == 1 else 0)
        counts[2, 2] = 1 if board[4, 7] == 1 else 0
        counts[3, 2] = np.sum(board[3:6:2, 6:9:2] == 1)

        # west
        counts[0, 3] = (1 if board[4, 0] == 1 else 0) + (1 if board[4, 2] == 1 else 0)
        counts[1, 3] = (1 if board[3, 1] == 1 else 0) + (1 if board[5, 1] == 1 else 0)
        counts[2, 3] = 1 if board[4, 1] == 1 else 0
        counts[3, 3] = np.sum(board[3:6:2, 0:3:2] == 1)

        # centre
        counts[0, 4] = 1 if board[4, 4] == 1 else 0
        counts[1, 4] = np.sum(board[3:6:2, 3:6:2] == 1)
        counts[2, 4] = (1 if board[4, 3] == 1 else 0) + (1 if board[4, 5] == 1 else 0)
        counts[3, 4] = (1 if board[3, 4] == 1 else 0) + (1 if board[5, 4] == 1 else 0)

        return counts

    @staticmethod
    def phase_relations(board):
        """Returns phase relations for pegs along three north-east diagonals and three south-east diagonals. See
        Beasley, The Ins and Outs of Peg Solitaire, Chapter 4."""

        pegs = np.nonzero(board == 1)
        ne_indx = np.mod(pegs[0] + pegs[1], 3)
        se_indx = np.mod(9 + pegs[0] - pegs[1], 3)
        parity = np.empty((6,), dtype=np.int8)
        for i in range(3):
            parity[i] = np.count_nonzero(ne_indx == i)
            parity[3+i] = np.count_nonzero(se_indx == i)

        return np.mod(parity, 2) == len(pegs[0]) % 2

    def save(self, fh):
        """Save state to a given file handle."""
        np.save(fh, self.init_state)
        np.save(fh, self.goal)
        np.save(fh, self.board)
        np.save(fh, self.moves)
        fh.write((1 if self.allow_symmetric else 0).to_bytes(4, 'big'))

    def load(self, fh):
        """Load state from a given file handle."""
        self.init_state = np.load(fh)
        self.goal = np.load(fh)
        self.board = np.load(fh)
        self.moves = np.load(fh)
        self.allow_symmetric = int.from_bytes(fh.read(4), 'big') != 0
        self.init_count = np.count_nonzero(self.init_state == 1)
        self.goal_count = np.count_nonzero(self.goal == 1)
        self.count = np.count_nonzero(self.board == 1)

    def move(self, i, j, d):
        """Execute a jump from (i,j) in direction d. Returns new GameState if successful and None otherwise."""
        #assert (0 <= i < 9) and (0 <= j < 9) and (0 <= d < 4)

        # check that position contains a marble
        if self.board[i, j] != 1:
            return None

        di, dj = GameState.dir2delta(d)

        # check move stays within board
        if not (0 <= i + 2 * di < 9) or not (0 <= j + 2 * dj < 9):
            return None

        # check that there exists a marble to jump and that the destination is empty
        if (self.board[i + di, j + dj] != 1) or (self.board[i + 2 * di, j + 2 * dj] != 0):
           return None

        # make the move
        state = copy.deepcopy(self)
        state.board[i, j] = 0
        state.board[i + di, j + dj] = 0
        state.board[i + 2 * di, j + 2 * dj] = 1
        state.count = self.count - 1
        state.moves[self.init_count - self.count] = (i, j, d)

        return state

    def is_solved(self):
        """Returns True if solved and False otherwise."""
        if self.count != self.goal_count:
            return False
        if self.allow_symmetric:
            return GameState.symmetric_cmp_eq(self.board, self.goal)
        return np.array_equal(self.board, self.goal)

    def is_impossible(self, check_phase_relations=False):
        """Returns True if impossible to solve and False if maybe possible to solve."""
        # check if already solved
        if self.is_solved():
            return False

        # check peg counts
        if (self.count <= self.goal_count):
            return True

        # check class counts
        board_classes = GameState.count_classes(self.board)
        goal_classes = GameState.count_classes(self.goal)
        if np.any(board_classes < goal_classes) and (not self.allow_symmetric or np.any(board_classes < GameState.count_classes(self.goal.T))):
            return True

        # legal moves (C/D classes can only take A/B classes and vice versa)
        if (np.sum(board_classes[2:4]) == 0) or (np.sum(board_classes[0:2]) == 0):
            return True

        # TODO: deal with symmetric case later
        if self.allow_symmetric:
            return check_phase_relations and np.any(GameState.phase_relations(self.board) != GameState.phase_relations(self.goal))

        # UNCOMMENT NEXT LINE TO SKIP ADDITIONAL CHECKS
        #return check_phase_relations and np.any(GameState.phase_relations(self.board) != GameState.phase_relations(self.goal))

        # check pegs/holes trapped in top, bottom, left and right 3x3 blocks
        if board_classes[0] == 0: # no A's
            if (self.board[1, 4] != self.goal[1, 4]):
                return True
            if (self.board[7, 4]  != self.goal[7, 4]):
                return True
            if (self.board[4, 1] != self.goal[4, 1]):
                return True
            if (self.board[4, 7] != self.goal[4, 7]):
                return True
                    
        if board_classes[1] == 0: # no B's
            if np.sum(self.board[0:3:2, 1::2] == 1) > np.sum(self.goal[0:3:2, 1::2] == 1):
                return True
            if np.sum(self.board[6::2, 1::2] == 1) > np.sum(self.goal[6::2, 1::2] == 1):
                return True
            if np.sum(self.board[1::2, 0:3:2] == 1) > np.sum(self.goal[1::2, 0:3:2] == 1):
                return True
            if np.sum(self.board[1::2, 6::2] == 1) > np.sum(self.goal[1::2, 6::2] == 1):
                return True

        if board_classes[2] == 0: # no C's
            if np.sum(self.board[1, (3,5)] == 1) != np.sum(self.goal[1, (3,5)] == 1):
                return True
            if np.sum(self.board[7, (3,5)] == 1) != np.sum(self.goal[7, (3,5)] == 1):
                return True
            if ((self.board[4, 0] == 1) and (self.goal[4, 0] != 1)) or ((self.board[4, 2] == 1) and (self.goal[4, 2] != 1)):
                return True
            if ((self.board[4, 6] == 1) and (self.goal[4, 6] != 1)) or ((self.board[4, 8] == 1) and (self.goal[4, 8] != 1)):
                return True

        if board_classes[3] == 0: # no D's
            if ((self.board[0, 4] == 1) and (self.goal[0, 4] != 1)) or ((self.board[2, 4] == 1) and (self.goal[2, 4] != 1)):
                return True
            if ((self.board[6, 4] == 1) and (self.goal[6, 4] != 1)) or ((self.board[8, 4] == 1) and (self.goal[8, 4] != 1)):
                return True
            if np.sum(self.board[(3,5), 1] == 1) != np.sum(self.goal[(3,5), 1] == 1):
                return True
            if np.sum(self.board[(3,5), 7] == 1) != np.sum(self.goal[(3,5), 7] == 1):
                return True

        # check class horizontal and vertical distances to goal state
        # e.g., if an A peg is two horizontal jumps an one vertical jump away from the goal then it needs at least two
        # C pegs and one D peg to get there
        # TODO: why does standard 45-hole game process more moves when aborting on the conditions below? unstable heap?
        # TODO: use hungarian matching for multi-peg goal state to avoid two goal states selecting same nearest peg

        # UNCOMMENT NEXT LINE TO SKIP ADDITIONAL CHECKS
        #return check_phase_relations and np.any(GameState.phase_relations(self.board) != GameState.phase_relations(self.goal))

        pegsA = np.nonzero(self.board[0::2, 0::2] == 1)
        pegsB = np.nonzero(self.board[1::2, 1::2] == 1)
        pegsC = np.nonzero(self.board[0::2, 1::2] == 1)
        pegsD = np.nonzero(self.board[1::2, 0::2] == 1)
        goalA = np.nonzero(self.goal[0::2, 0::2] == 1)
        goalB = np.nonzero(self.goal[1::2, 1::2] == 1)
        goalC = np.nonzero(self.goal[0::2, 1::2] == 1)
        goalD = np.nonzero(self.goal[1::2, 0::2] == 1)

        # check enough C pegs for horizontal distance to A and vertical distance to B
        if ((0 if len(goalA[1]) == 0 else np.sum(np.min(np.abs(pegsA[1] - goalA[1][:, None]), axis=1))) +
            (0 if len(goalB[0]) == 0 else np.sum(np.min(np.abs(pegsB[0] - goalB[0][:, None]), axis=1)))) > board_classes[2]:
            return True

        # check enough D pegs for vertical distance to A and horizontal distance to B
        if ((0 if len(goalA[0]) == 0 else np.sum(np.min(np.abs(pegsA[0] - goalA[0][:, None]), axis=1))) +
            (0 if len(goalB[1]) == 0 else np.sum(np.min(np.abs(pegsB[1] - goalB[1][:, None]), axis=1)))) > board_classes[3]:
            return True

        # check enough A pegs for horizontal distance to C and vertical distance to D
        if ((0 if len(goalC[1]) == 0 else np.sum(np.min(np.abs(pegsC[1] - goalC[1][:, None]), axis=1))) +
            (0 if len(goalD[0]) == 0 else np.sum(np.min(np.abs(pegsD[0] - goalD[0][:, None]), axis=1)))) > board_classes[0]:
            return True

        # check enough B pegs for vertical distance to C and horizontal distance to D
        if ((0 if len(goalC[0]) == 0 else np.sum(np.min(np.abs(pegsC[0] - goalC[0][:, None]), axis=1))) +
            (0 if len(goalD[1]) == 0 else np.sum(np.min(np.abs(pegsD[1] - goalD[1][:, None]), axis=1)))) > board_classes[1]:
            return True

        # check non-goal D pegs can be cleared
        if (goal_classes[3] == 0) and (board_classes[3] != 0):
            existA, existB = False, False
            if (board_classes[0] != 0):
                v = np.logical_and(np.abs(2 * pegsA[0] - (2 * pegsD[0][:, None] + 1)) <= 2 * board_classes[3],
                                   np.abs(2 * pegsA[1] - 2 * pegsD[1][:, None]) <= 2 * board_classes[2] + 1)
                existA = np.any(v, axis=1)

            if (board_classes[1] != 0):
                v = np.logical_and(np.abs((2 * pegsB[1] + 1) - 2 * pegsD[1][:, None]) <= 2 * board_classes[3],
                                   np.abs((2 * pegsB[0] + 1) - (2 * pegsD[0][:, None] + 1)) <= 2 * board_classes[2] + 1)
                existB = np.any(v, axis=1)

            if not np.all(np.logical_or(existA, existB)):
                #print("\n--- can't clear D pegs ---"); print(self); print("---")
                return True

        # check non-goal C pegs can be cleared
        if (goal_classes[2] == 0) and (board_classes[2] != 0):
            existA, existB = False, False
            if (board_classes[0] != 0):
                v = np.logical_and(np.abs(2 * pegsA[1] - (2 * pegsC[1][:, None] + 1)) <= 2 * board_classes[2],
                                   np.abs(2 * pegsA[0] - 2 * pegsC[0][:, None]) <= 2 * board_classes[3] + 1)
                existA = np.any(v, axis=1)

            if (board_classes[1] != 0):
                v = np.logical_and(np.abs((2 * pegsB[0] + 1) - 2 * pegsC[0][:, None]) <= 2 * board_classes[2],
                                   np.abs((2 * pegsB[1] + 1) - (2 * pegsC[1][:, None] + 1)) <= 2 * board_classes[3] + 1)
                existB = np.any(v, axis=1)

            if not np.all(np.logical_or(existA, existB)):
                #print("\n--- can't clear C pegs ---"); print(self); print("---")
                return True

        # check non-goal B pegs can be cleared
        if (goal_classes[1] == 0) and (board_classes[1] != 0):
            existC, existD = False, False
            if (board_classes[2] != 0):
                v = np.logical_and(np.abs(2 * pegsC[0] - (2 * pegsB[0][:, None] + 1)) <= 2 * board_classes[1],
                                   np.abs((2 * pegsC[1] + 1) - (2 * pegsB[1][:, None] + 1)) <= 2 * board_classes[0] + 1)
                existC = np.any(v, axis=1)

            if (board_classes[3] != 0):
                v = np.logical_and(np.abs(2 * pegsD[1] - (2 * pegsB[1][:, None] + 1)) <= 2 * board_classes[1],
                                   np.abs((2 * pegsD[0] + 1) - (2 * pegsB[0][:, None] + 1)) <= 2 * board_classes[0] + 1)
                existD = np.any(v, axis=1)

            if not np.all(np.logical_or(existC, existD)):
                #print("\n--- can't clear B pegs ---"); print(self); print("---")
                return True

        # check non-goal A pegs can be cleared
        if (goal_classes[0] == 0) and (board_classes[0] != 0):
            existC, existD = False, False
            if (board_classes[2] != 0):
                v = np.logical_and(np.abs((2 * pegsC[1] + 1) - 2 * pegsA[1][:, None]) <= 2 * board_classes[0],
                                   np.abs(2 * pegsC[0] - 2 * pegsA[0][:, None]) <= 2 * board_classes[1] + 1)
                existC = np.any(v, axis=1)

            if (board_classes[3] != 0):
                v = np.logical_and(np.abs((2 * pegsD[0] + 1) - 2 * pegsA[0][:, None]) <= 2 * board_classes[0],
                                   np.abs(2 * pegsD[1] - 2 * pegsA[1][:, None]) <= 2 * board_classes[1] + 1)
                existD = np.any(v, axis=1)

            if not np.all(np.logical_or(existC, existD)):
                #print("\n--- can't clear A pegs ---"); print(self); print("---")
                return True

        # check phase relations (Beasley, pp. 54--56)
        return check_phase_relations and np.any(GameState.phase_relations(self.board) != GameState.phase_relations(self.goal))

    def iou(self):
        """Returns the intersection over union of the board state and the goal state."""
        intersection = np.sum(np.logical_and(self.board == 1, self.goal == 1))
        union = np.sum(np.logical_or(self.board == 1, self.goal == 1))
        return intersection / union

    def bounding_area(self):
        """Returns area bounding box around board and goal."""
        union =  np.transpose(np.nonzero(np.logical_or(self.board == 1, self.goal == 1)))
        return np.prod(np.max(union, axis=0) - np.min(union, axis=0) + 1)

    def counts_in_bounding_area(self):
        """Returns count of illegal, empty and pegs in bounding box around board and goal."""
        union =  np.transpose(np.nonzero(np.logical_or(self.board == 1, self.goal == 1)))
        ub = np.max(union, axis=0)
        lb = np.min(union, axis=0)
        n_illegal = np.sum(self.board[lb[0]:ub[0]+1, lb[1]:ub[1]+1] == -1)
        n_empty = np.sum(self.board[lb[0]:ub[0]+1, lb[1]:ub[1]+1] == 0)
        n_pegs = np.sum(self.board[lb[0]:ub[0]+1, lb[1]:ub[1]+1] == 1)
        return n_illegal, n_empty, n_pegs

    def __eq__(self, other):
        """Equality operator. Checks for rotation and reflection symmetries."""
        if (self.count != other.count):
            return False
        if self.allow_symmetric:
            return GameState.symmetric_cmp_eq(self.board, other.board)
        return np.array_equal(self.board, other.board)

    def __lt__(self, other):
        return self.count < other.count

    def __str__(self):
        return "\n".join(["".join(["*" if self.init_state[i, j] == 1 else "." if self.init_state[i, j] == 0 else " " for j in range(9)]) + \
            "\t" + "".join([(("A", "C"), ("D", "B"))[i % 2][j % 2] if self.board[i, j] == 1 else "." if self.board[i, j] == 0 else " " for j in range(9)]) + \
            "\t" + "".join(["X" if self.goal[i, j] == 1 else "." if self.goal[i, j] == 0 else " " for j in range(9)]) for i in range(9)])

    def __hash__(self):
        """Hash function needed for insertion into a set."""
        return int(np.sum(np.where(self.board == 1, GameState.hash_indx, 0)))


class SearchState:
    """State of the search."""

    def __init__(self):
        self.movesEvaluated = 0
        self.movesSkipped = 0
        self.frontier = []
        self.seen = set()
        self.bestGameFound = None

    def print(self, game=None):
        """Prints search state."""
        if game is None:
            game = self.bestGameFound
        if self.frontier:
            min_game = min([g.count for (s, g) in self.frontier])
            max_game = max([g.count for (s, g) in self.frontier])
        else:
            min_game, max_game = 0, 0
        print("\rat {}, tried {} moves, skipped {} moves, {} marbles remaining, {:0.3f} IoU, {} games in frontier ({}--{} pegs)".format(
                time.asctime(), self.movesEvaluated, self.movesSkipped, game.count if game else 45, game.iou(), len(self.frontier), min_game, max_game), end="")

    def write(self, filename):
        """Write state to file."""
        with open(filename, 'wb') as file:
            file.write(self.movesEvaluated.to_bytes(4, 'big'))
            file.write(self.movesSkipped.to_bytes(4, 'big'))
            file.write((len(self.frontier)).to_bytes(4, 'big'))
            for score, game in self.frontier:
                file.write(score.to_bytes(4, 'big'))
                game.save(file)
            file.write((len(self.seen)).to_bytes(4, 'big'))
            for game in self.seen:
                game.save(file)
            if self.bestGameFound is not None:
                self.bestGameFound.save(file)
            else:
                game = GameState()
                game.save(file)

    def read(self, filename):
        """Read state from a file."""
        with (open(filename, 'rb') as file):
            self.movesEvaluated = int.from_bytes(file.read(4), 'big')
            self.movesSkipped = int.from_bytes(file.read(4), 'big')
            n = int.from_bytes(file.read(4), 'big')
            print("...reading {} frontier games".format(n))
            self.frontier = []
            for i in range(n):
                score = int.from_bytes(file.read(4), 'big')
                game = GameState()
                game.load(file)
                self.frontier.append((score, game))

            n = int.from_bytes(file.read(4), 'big')
            print("...reading {} seen games".format(n))
            self.seen = set()
            for i in range(n):
                game = GameState()
                game.load(file)
                if game in self.seen:
                    print(game)
                    assert False
                self.seen.add(game)
            assert len(self.seen) == n

            self.bestGameFound = GameState()
            self.bestGameFound.load(file)


def getLaTeXHeader():
    """Returns header for LaTeX/TikZ source."""

    return r"""\documentclass[10pt,a4paper]{article}        
    \usepackage{pgfplots}
    \pgfplotsset{compat=1.5}
    \usepackage{tikz, tikzscale, ifthen}
    \usetikzlibrary{arrows.meta}

    \usepackage[cm]{fullpage}
	\pagenumbering{gobble}
	
    \begin{document}

        \newcommand{\drawboard}[1]{ % 2d board array (-1: illegal, 0: empty, 1: occupied, 2: src, 3: dst)
            \draw[thin, black!30, fill=black!10] (5, 5) circle (5cm);
            \foreach \x in {1,2,...,9}{
                \foreach \y in {1,2,...,9}{
                    \pgfmathsetmacro{\value}{int(#1[9-\y][\x-1])}
                    \pgfmathparse{\value == 0}\ifdim\pgfmathresult pt>0pt\draw[thin, black!50, fill=black!10] (\x, \y) circle (3.5mm);\fi
                    \pgfmathparse{\value == 1}\ifdim\pgfmathresult pt>0pt\draw[thin, black!50, fill=black!50] (\x, \y) circle (3.5mm);\fi
                    \pgfmathparse{\value == 2}\ifdim\pgfmathresult pt>0pt\draw[thin, red!50, fill=red!50] (\x, \y) circle (3.5mm);\fi
                    \pgfmathparse{\value == 3}\ifdim\pgfmathresult pt>0pt\draw[thin, red!50, fill=black!10] (\x, \y) circle (3.5mm);\fi
                }
            }
        }
        
        \newcommand{\drawlogoboard}[1]{ % 2d board array (-1: illegal, 0: empty, 1: occupied, 2: src, 3: dst)
			\draw[ultra thin, black] (5, 5) circle (5cm);
			\foreach \x in {1,2,...,9}{
				\foreach \y in {1,2,...,9}{
					\pgfmathsetmacro{\value}{int(#1[9-\y][\x-1])}
					\pgfmathparse{\value == 0}\ifdim\pgfmathresult pt>0pt\draw[ultra thin, black, fill=white] (\x, \y) circle (3.5mm);\fi
					\pgfmathparse{\value == 1}\ifdim\pgfmathresult pt>0pt\draw[ultra thin, black, fill=black] (\x, \y) circle (3.5mm);\fi
					\pgfmathparse{\value == 2}\ifdim\pgfmathresult pt>0pt\draw[ultra thin, black, fill=black] (\x, \y) circle (3.5mm);\fi
					\pgfmathparse{\value == 3}\ifdim\pgfmathresult pt>0pt\draw[ultra thin, black, fill=white] (\x, \y) circle (3.5mm);\fi
				}
			}
		}
    """

def getLaTeXFooter():
    """Returns footer for LaTeX/TikZ source."""
    return r"\end{document}"

def getLaTeXLogo(start, goal):
    """Returns LaTeX/TikZ source for logo of start and goal states."""

    init_str = r"{" + ", ".join([r"{" + ", ".join([str(start[i, j]) for j in range(9)]) + r"}" for i in range(9)]) + r"}"
    goal_str = r"{" + ", ".join([r"{" + ", ".join([str(goal[i, j]) for j in range(9)]) + r"}" for i in range(9)]) + r"}"

    return r"""
        \AddToHookNext{shipout/foreground}{%
			\put(\paperwidth-3cm,-1.5cm){%
				\begin{tikzpicture}[scale=0.1]
					\begin{scope}[xshift=0cm, yshift=0cm]
						\drawlogoboard{""" + init_str + r"""};
					\end{scope}
					\begin{scope}[xshift=15cm, yshift=0cm]
						\drawlogoboard{""" + goal_str + r"""};
					\end{scope}
					\draw[black, -{LaTeX[]}] (9cm,9cm) [out=30, in=150] to (16cm,9cm);
				\end{tikzpicture}%
			}%
		}
    """


def getLaTeXGame(game):
    """Returns the history of game moves as LaTeX/TikZ source."""

    out_str = r"""
        \vspace*{\fill}
        \begin{center}
            \begin{tikzpicture}[scale=0.25]
    """

    g = GameState(init_state = game.init_state, goal_state=game.goal)
    count = 0
    for i, j, d in game.moves[:game.init_count - game.count]:
        board = copy.deepcopy(g.board)
        board[i, j] = 2
        di, dj = GameState.dir2delta(d)
        board[i + 2*di, j + 2*dj] = 3
        board_string = r"{" + ", ".join([r"{" + ", ".join([str(board[i, j]) for j in range(9)]) + r"}" for i in range(9)]) + r"}"

        out_str += "\t\\begin{{scope}}[xshift={}cm, yshift={}cm]\n".format(12*(count % 6), -12 * int(count / 6))
        out_str += "\t\t\\drawboard{" + board_string + "};\n"
        out_str += "\t\\end{scope}\n"

        g = g.move(i, j, d)
        count += 1

    board_string = r"{" + ", ".join([r"{" + ", ".join([str(g.board[i, j]) for j in range(9)]) + r"}" for i in range(9)]) + r"}"
    out_str += "\t\\begin{{scope}}[xshift={}cm, yshift={}cm]\n".format(12 * (count % 6), -12 * int(count / 6))
    out_str += "\t\t\\drawboard{" + board_string + "};\n"
    out_str += "\t\\end{scope}"

    out_str += r"""
            \end{tikzpicture}
        \end{center}
        \vspace*{\fill}    
    """

    return out_str


def expandGame(game):
    """Expands a game returning all possible next moves."""

    expanded_games = []
    for i, j in zip(*np.nonzero(game.board == 1)):
        for d in range(4):
            # try making a move and add to return list if successful
            attempt = game.move(i, j, d)
            if attempt is not None:
                expanded_games.append(attempt)

    return expanded_games


def prioritySearch(init_state=None, goal_state=None, allow_symmetric=True, maxMoves=None):
    """Search for a solution using a priority queue ('frontier') to maintain partial games. Skips any game already
    added to the queue or previously processed from the queue ('seen')."""

    print("started at {}...".format(time.asctime()))

    # initialize the search state
    search = SearchState()
    game = GameState(init_state, goal_state, allow_symmetric)
    print(game)
    if game.is_impossible(check_phase_relations=True):
        print("...game is impossible!")
        return game

    heapq.heappush(search.frontier, (0, game))
    search.seen.add(game)
    search.bestGameFound = game

    # keep processing partial games in the queue
    while (len(search.frontier)):
        search.movesEvaluated += 1
        score, game = heapq.heappop(search.frontier)

        # check if the game is solved or maximum number of moves has been reached
        if game.is_solved():
            search.bestGameFound = game
            search.print()
            print("\n...{}\n".format([(i + 1, j + 1, GameState.dir2str(d)) for i, j, d in game.moves]), end="")
            break
        if (maxMoves is not None) and (search.movesEvaluated >= maxMoves):
            break

        # look for legal moves from the current game
        legalMove = False
        for attempt in expandGame(game):
            if attempt.is_impossible():
                search.movesSkipped += 1
            elif attempt in search.seen:
                search.movesSkipped += 1
            else:
                legalMove = True
                #score = attempt.bounding_area() - attempt.count
                #score = attempt.count

                n_i, n_e, n_p = attempt.counts_in_bounding_area()
                score = n_e * n_p

                if (attempt.count - attempt.goal_count <= 3):
                    score = 0

                heapq.heappush(search.frontier, (int(score), attempt))
                search.seen.add(attempt)

        # if a legal move could not be made print some progress statistics and updated the best game found so far
        if not legalMove:
            search.print(game)
            if game.iou() > search.bestGameFound.iou():
                search.bestGameFound = game
                print("\n...{}\n".format([(i+1, j+1, GameState.dir2str(d)) for i, j, d in game.moves[:game.init_count-game.count]]), end="")
                print(game)

    print(game)
    print("...solution found!" if search.bestGameFound.is_solved() else "...not solved!")

    # UNCOMMENT TO SAVE SEARCH STATE
    #filename = "peg_search_state.bin"
    #print("writing search state to {} ...".format(filename))
    #search.write(filename)

    return search.bestGameFound


def searchAll(init_state=None, goal_state=None, maxMoves=None):
    """Search for all solutions using a queue ('frontier') to maintain partial games."""

    print("started at {}...".format(time.asctime()))

    # initialize the search state
    search = SearchState()
    solutions = []
    game = GameState(init_state, goal_state, False)
    print(game)
    if game.is_impossible(check_phase_relations=True):
        print("...game is impossible!")
        return solutions

    search.frontier.append((0, game))

    # keep processing partial games in the queue
    while (len(search.frontier)):
        search.movesEvaluated += 1
        _, game = search.frontier.pop()

        # check if the game is solved or maximum number of moves has been reached
        if game.is_solved():
            solutions.append(game)
            search.print(game)
            print("\n...{}\n".format([(i + 1, j + 1, GameState.dir2str(d)) for i, j, d in game.moves]), end="")
            print("...{} solutions found so far".format(len(solutions)))
            continue
        if (maxMoves is not None) and (search.movesEvaluated >= maxMoves):
            break

        # look for legal moves from the current game
        legalMove = False
        for attempt in expandGame(game):
            if attempt.is_impossible():
                search.movesSkipped += 1
            else:
                legalMove = True
                search.frontier.append((0, attempt))

        # if a legal move could not be made print some progress statistics and updated the best game found so far
        if not legalMove:
            search.print(game)

    print("...{} total solutions found!".format(len(solutions)))
    return solutions


if __name__ == "__main__":

    # testing
    if False:
        start = GameState.set(GameState.fill(0, 45), ((4, 6), (4, 4), (4, 2), (4, 1), (0, 4), (7, 4)))
        goal = GameState.set(GameState.fill(0, 45), ((4, 7), (8, 4)))

        game = GameState(init_state=start, goal_state=goal, allow_symmetric=False)
        print(game)
        print(game.is_impossible())

        #game = prioritySearch(init_state=start, goal_state=goal, allow_symmetric=False)

        start[0, 4] = 0
        start[6, 4] = 1

        game = GameState(init_state=start, goal_state=goal, allow_symmetric=False)
        print(game)
        print(game.is_impossible())

        #game = prioritySearch(init_state=start, goal_state=goal, allow_symmetric=False)

        start = GameState.set(GameState.fill(0, 45), ((3, 2), (3, 5), (4, 4), (5, 2), (5, 8)))
        goal = GameState.set(GameState.fill(0, 45), ((4, 4),))
        game = GameState(init_state=start, goal_state=goal, allow_symmetric=False)
        print(game)
        print(game.is_impossible())

        start = GameState.set(GameState.fill(0, 45), ((3, 0), (3, 3), (4, 4)))
        goal = GameState.set(GameState.fill(0, 45), ((4, 4),))
        game = GameState(init_state=start, goal_state=goal, allow_symmetric=False)
        print(game)
        print(game.is_impossible())

        exit(0)

    # 33-hole standard game all solutions
    if True:
        start = GameState.fill(1, 33)
        start[4, 4] = 0

        goal = np.where(start == -1, -1, 0)
        goal[4, 4] = 1

        solutions = searchAll(init_state=start, goal_state=goal)

        filename = "solutions33.bin"
        print("writing {} solutions to {} ...".format(filename))
        with open(filename, 'wb') as file:
            file.write((len(solutions)).to_bytes(4, 'big'))
            for game in solutions:
                game.save(file)

        exit(0)

    # 45-hole standard game
    if True:
        game = prioritySearch(allow_symmetric=False)

        filename = "pegs45.tex"
        print("writing LaTeX to {} ...".format(filename))
        with open(filename, 'wt') as file:
            file.write(getLaTeXHeader())
            file.write("\n\t" + r"\begin{center} {\Huge 45-Hole Peg Solitaire} \end{center}" + "\n")
            file.write(getLaTeXGame(game))
            file.write(getLaTeXFooter())

        game_filename = "pegs45.bin"
        print("writing game to {} ...".format(game_filename))
        with open(game_filename, 'wb') as file:
            game.save(file)

        exit(0)

    # 33-hole standard game
    if False:
        start = GameState.fill(1, 33)
        start[4, 4] = 0

        goal = np.where(start == -1, -1, 0)
        goal[4, 4] = 1

        game = prioritySearch(init_state=start, goal_state=goal, allow_symmetric=True)

        filename = "pegs33.tex"
        print("writing LaTeX to {} ...".format(filename))
        with open(filename, 'wt') as file:
            file.write(getLaTeXHeader())
            file.write("\n\t" + r"\begin{center} {\Huge 33-Hole Peg Solitaire} \end{center}" + "\n")
            file.write(getLaTeXGame(game))
            file.write(getLaTeXFooter())

    # 33-hole corner game
    if False:
        start = GameState.fill(1, 33)
        start[4, 4] = 0

        goal = np.where(start == -1, -1, 1 - start)
        #goal[1, 3] = goal[1, 4] = goal[1, 5] = 1
        #goal[7, 3] = goal[7, 4] = goal[7, 5] = 1
        #goal[3, 1] = goal[4, 1] = goal[5, 1] = 1
        #goal[3, 7] = goal[4, 7] = goal[5, 7] = 1

        goal[1, 3] = goal[1, 5] = 1
        goal[7, 3] = goal[7, 5] = 1
        goal[3, 1] = goal[5, 1] = 1
        goal[3, 7] = goal[5, 7] = 1

        filename = "pegs33.tex"
        print("writing LaTeX to {} ...".format(filename))
        with open(filename, 'wt') as file:
            file.write(getLaTeXHeader())

            game = prioritySearch(start, goal, True)
            file.write(getLaTeXLogo(start, goal))
            file.write(getLaTeXGame(game))
            file.write(getLaTeXFooter())

        exit(0)

    # 45-hole corner game
    if False:
        start = GameState.fill(1, 45)
        start[4, 4] = 0

        goal = np.where(start == -1, -1, 1 - start)
        goal[0, 3] = goal[0, 5] = 1
        goal[8, 3] = goal[8, 5] = 1
        goal[3, 0] = goal[5, 0] = 1
        goal[3, 8] = goal[5, 8] = 1

        filename = "pegs45c.tex"
        print("writing LaTeX to {} ...".format(filename))
        with open(filename, 'wt') as file:
            file.write(getLaTeXHeader())

            game = prioritySearch(start, goal, True)
            file.write(getLaTeXLogo(start, goal))
            file.write(getLaTeXGame(game))
            file.write(getLaTeXFooter())

        exit(0)

    # 45-hole single-vacancy games
    if True:
        filename = "pegs45a.tex"
        print("writing LaTeX to {} ...".format(filename))
        with open(filename, 'wt') as file:
            file.write(getLaTeXHeader())
            file.write("\n\t\t" + r"\begin{center} {\Huge 45-Hole Peg Solitaire} \\ {\Large single-vacancy complement problems} \end{center}" + "\n")

            for location in ((4, 4), (4, 3), (4, 2), (4, 1), (4, 0), (5, 3), (5, 2), (5, 1), (5, 0)):
                file.write("\n\t\t" + r"\newpage" + "\n")

                start = GameState.fill(1)
                start[location] = 0

                goal = np.where(start == -1, -1, 0)
                goal[location] = 1

                file.write(getLaTeXLogo(start, goal))
                game = prioritySearch(init_state=start, goal_state=goal, allow_symmetric=False, maxMoves=10000000)
                if game.is_solved():
                    file.write(getLaTeXGame(game))
                else:
                    file.write(r"""\vspace*{\fill}\begin{center}no solution\end{center}\vspace*{\fill}""" + "\n")
                    # TODO: show best game found
                    
            file.write(getLaTeXFooter())

        exit(0)

    # 33-hole games
    if True:
        filename = "pegs33a.tex"
        print("writing LaTeX to {} ...".format(filename))
        with open(filename, 'wt') as file:
            file.write(getLaTeXHeader())
            file.write("\n\t\t" + r"\begin{center} {\Huge 33-Hole Peg Solitaire} \\ {\Large single-vacancy complement problems} \end{center}" + "\n")

            for location in ((4, 4), (4, 3), (4, 2), (4, 1), (5, 3), (5, 2), (5, 1)):
                file.write("\n\t\t" + r"\newpage" + "\n")

                start = GameState.fill(1, 33)
                start[location] = 0

                goal = np.where(start == -1, -1, 0)
                goal[location] = 1

                file.write(getLaTeXLogo(start, goal))
                game = prioritySearch(init_state=start, goal_state=goal, allow_symmetric=False)
                if game.is_solved():
                    file.write(getLaTeXGame(game))
                else:
                    file.write(r"""\vspace*{\fill}\begin{center}no solution\end{center}\vspace*{\fill}""" + "\n")

            file.write(getLaTeXFooter())

