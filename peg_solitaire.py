# 9x9 PEG SOLITAIRE
# Stephen Gould
#
#                   (0,3) (0,4) (0,5)
#                   (1,3) (1,4) (1,5)
#                   (2,3) (2,4) (2,5)
# (3,0) (3,1) (3,2) (3,3) (3,4) (3,5) (3,6) (3,7) (3,8)
# (4,0) (4,1) (4,2) (4,3) (4,4) (4,5) (4,6) (4,7) (4,8)
# (5,0) (5,1) (5,2) (5,3) (5,4) (5,5) (5,6) (5,7) (5,8)
#                   (6,3) (6,4) (6,5)
#                   (7,3) (7,4) (7,5)
#                   (8,3) (8,4) (8,5)
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
            self.board = np.array([[-1 if ((i < 3) or (i > 5)) and ((j < 3) or (j > 5)) else 1 for j in range(9)] for i in range(9)], dtype=np.int8)
            self.board[4, 4] = 0
        else:
            self.board = init_state

        if goal_state is None:
            self.goal = np.array([[-1 if ((i < 3) or (i > 5)) and ((j < 3) or (j > 5)) else 0 for j in range(9)] for i in range(9)], dtype=np.int8)
            self.goal[4, 4] = 1
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
    def empty():
        """Returns an empty board."""
        return np.array([[-1 if ((i < 3) or (i > 5)) and ((j < 3) or (j > 5)) else 0 for j in range(9)] for i in range(9)], dtype=np.int8)

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
        m = np.sum(np.logical_and(pegs[0] == 0, pegs[1] == 0))
        c = np.sum(np.logical_and(pegs[0] == 1, pegs[1] == 1))
        s = np.sum(np.logical_and(pegs[0] == 0, pegs[1] == 1))
        t = np.sum(np.logical_and(pegs[0] == 1, pegs[1] == 0))

        return np.array([m, c, s, t], dtype=np.int8)

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
        return np.array_equal(self.board, self.goal)

    def is_impossible(self):
        """Returns True if impossible to solve and False if maybe possible to solve."""
        board_counts = GameState.count_classes(self.board)
        return np.any(board_counts < GameState.count_classes(self.goal)) and \
            (not self.allow_symmetric or np.any(board_counts < GameState.count_classes(self.goal.T)))

    def iou(self):
        """Returns the intersection over union of the board state and the goal state."""
        intersection = np.sum(np.logical_and(self.board == 1, self.goal == 1))
        union = np.sum(np.logical_or(self.board == 1, self.goal == 1))
        return intersection / union

    def bounding_area(self):
        """Returns area bounding box around board and goal."""
        union =  np.transpose(np.nonzero(np.logical_or(self.board == 1, self.goal == 1)))
        return np.prod(np.max(union, axis=0) - np.min(union, axis=0) + 1)

    def __eq__(self, other):
        """Equality operator. Checks for rotation and reflection symmetries."""
        if (self.count != other.count):
            return False
        if np.array_equal(self.board, other.board):
            return True

        if (self.allow_symmetric):
            other_transposed = np.transpose(other.board)
            if np.array_equal(self.board, other_transposed):
                return True

            b = np.fliplr(self.board)
            if np.array_equal(b, other.board):
                return True
            if np.array_equal(b, other_transposed):
                return True
            b = np.flipud(b)
            if np.array_equal(b, other.board):
                return True
            if np.array_equal(b, other_transposed):
                return True
            b = np.fliplr(b)
            if np.array_equal(b, other.board):
                return True
            if np.array_equal(b, other_transposed):
                return True

        return False

    def __lt__(self, other):
        return self.count < other.count

    def __str__(self):
        return "\n".join(["".join(["X" if self.board[i, j] == 1 else "." if self.board[i, j] == 0 else " " for j in range(9)]) for i in range(9)])

    def __hash__(self):
        """Hash function needed for insertion into a set."""
        return int(np.sum(np.where(self.board == 1, GameState.hash_indx, 0)))
        #return int(np.dot(GameState.count_classes(self.board), np.array([1, 12, 144, 144])))


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
        print("\rtried {} moves, skipped {} moves, {} marbles remaining, {:0.3f} IoU, {} games in frontier, {}/{} smallest/biggest game in frontier".format(
                self.movesEvaluated, self.movesSkipped, game.count if game else 45, game.iou(), len(self.frontier),
            min([g.count for (s, g) in self.frontier]), max([g.count for (s, g) in self.frontier])), end="")


def gameMoves2Latex(game):
    """Prints the history of game moves as LaTeX/TikZ source."""

    out_str = r"""
    \newcommand{\drawboard}[1]{ % 2d board array (-1: illegal, 0: empty, 1: occupied, 2: src, 3: dst)
        \draw[black!30, fill=black!10] (5, 5) circle (5cm);
        \foreach \x in {1,2,...,9}{
            \foreach \y in {1,2,...,9}{
                \pgfmathsetmacro{\value}{int(#1[9-\y][\x-1])}
                \pgfmathparse{\value == 0}\ifdim\pgfmathresult pt>0pt\draw[black!50, fill=black!10] (\x, \y) circle (4mm);\fi
  			    \pgfmathparse{\value == 1}\ifdim\pgfmathresult pt>0pt\draw[white!50, fill=black!50] (\x, \y) circle (4mm);\fi
			    \pgfmathparse{\value == 2}\ifdim\pgfmathresult pt>0pt\draw[white!50, fill=red!50] (\x, \y) circle (4mm);\fi
                \pgfmathparse{\value == 3}\ifdim\pgfmathresult pt>0pt\draw[red!50, fill=black!10] (\x, \y) circle (4mm);\fi
            }
        }
    }
    
    \begin{center}
	    \begin{tikzpicture}[scale=0.25]
    """

    g = GameState()
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
    """

    return out_str


def prioritySearch(maxMoves=None):
    """Search for a solution using a priority queue ('frontier') to maintain partial games. Skips any game already
    added to the queue or previously processed from the queue ('seen')."""

    print("started at {}...".format(time.asctime()))

    # initialize the search state
    search = SearchState()
    game = GameState(allow_symmetric=True)
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
        for i, j in zip(*np.nonzero(game.board == 1)):
            for d in range(4):
                # try making a move
                attempt = game.move(i, j, d)
                if attempt is not None:
                    if attempt in search.seen:
                        search.movesSkipped += 1
                    elif attempt.is_impossible():
                        search.movesSkipped += 1
                    else:
                        legalMove = True
                        score = attempt.bounding_area() - attempt.count
                        heapq.heappush(search.frontier, (int(score), attempt))
                        search.seen.add(attempt)

        # if a legal move could not be made print some progress statistics and updated the best game found so far
        if not legalMove:
            search.print(game)
            if game.iou() > search.bestGameFound.iou():
                search.bestGameFound = game
                print("\n...{}\n".format([(i+1, j+1, GameState.dir2str(d)) for i, j, d in game.moves[:game.init_count-game.count]]), end="")

    return search.bestGameFound


if __name__ == "__main__":

    if False:
        game = GameState()
        print(GameState.count_classes(game.board))
        print(GameState.count_classes(game.goal))
        print(game.is_solved())
        print(game.is_impossible())
        exit(0)

    game = prioritySearch()
    #print(gameMoves2Latex(game))

