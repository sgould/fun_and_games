# 9x9 (45-HOLE) PEG SOLITAIRE
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
            self.init_state = np.array([[-1 if ((i < 3) or (i > 5)) and ((j < 3) or (j > 5)) else 1 for j in range(9)] for i in range(9)], dtype=np.int8)
            self.init_state[4, 4] = 0
        else:
            self.init_state = init_state
        self.board = np.copy(self.init_state)

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
        self.moves = np.empty((self.init_count, 3), dtype=np.int8)

    @staticmethod
    def fill(value = 0, n = 45):
        """Returns a board filled with 'value' for n-hole game ('n' can be 33 or 45)."""
        assert (n == 33) or (n == 45)
        board = np.array([[-1 if ((i < 3) or (i > 5)) and ((j < 3) or (j > 5)) else value for j in range(9)] for i in range(9)], dtype=np.int8)
        if n == 33:
            board[0, :] = board[8, :] = board[:, 0] = board[:, 8] = -1
        return board

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
        # check if already solved
        if self.is_solved():
            return False

        # check peg counts
        if (self.count <= self.goal_count) and (not self.is_solved()):
            return True

        # check class counts
        board_classes = GameState.count_classes(self.board)
        goal_classes = GameState.count_classes(self.goal)
        if np.any(board_classes < goal_classes) and (not self.allow_symmetric or np.any(board_classes < GameState.count_classes(self.goal.T))):
            return True

        # more class checks (s/t can only take m/c and vice versa)
        if ((np.sum(board_classes[2:4]) == 0) and (np.sum(goal_classes[0:2]) > 0)) or ((np.sum(board_classes[0:2]) == 0) and (np.sum(goal_classes[2:4]) > 0)):
            return True

        # check no legal moves
        #if (np.count_nonzero(board_classes) <= 1):
        #    return True

        # check phase relations (Beasley, pp. 54--56)
        return np.any(GameState.phase_relations(self.board) != GameState.phase_relations(self.goal))

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
        return "\n".join(["".join(["O" if self.board[i, j] == 1 else "." if self.board[i, j] == 0 else " " for j in range(9)]) + \
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
        print("\rat {}, tried {} moves, skipped {} moves, {} marbles remaining, {:0.3f} IoU, {} games in frontier, {}/{} smallest/biggest game in frontier".format(
                time.asctime(), self.movesEvaluated, self.movesSkipped, game.count if game else 45, game.iou(), len(self.frontier), min_game, max_game), end="")


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


def prioritySearch(init_state=None, goal_state=None, maxMoves=None):
    """Search for a solution using a priority queue ('frontier') to maintain partial games. Skips any game already
    added to the queue or previously processed from the queue ('seen')."""

    print("started at {}...".format(time.asctime()))

    # initialize the search state
    search = SearchState()
    game = GameState(init_state, goal_state)
    print(game)
    if game.is_impossible():
        print("...game is impossible!")
        return game

    heapq.heappush(search.frontier, (0, game))
    search.seen.add(game)
    search.bestGameFound = game

    # sort valid positions by hamming distance to goal state
    #valid = np.nonzero(game.board != -1)
    #goal_pegs = np.nonzero(game.goal == 1)
    #hamming = np.abs(valid[0] - goal_pegs[0][:, None]) + np.abs(valid[1] - goal_pegs[1][:, None])
    #order = np.transpose(np.transpose(valid)[np.argsort(np.min(hamming, axis=0))])

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
                    if attempt.is_impossible():
                        search.movesSkipped += 1
                    elif attempt in search.seen:
                        search.movesSkipped += 1
                    else:
                        legalMove = True
                        #score = 0 if (attempt.count - attempt.goal_count <= 3) else attempt.bounding_area() - attempt.count
                        #score = (attempt.bounding_area() - attempt.count) * (attempt.count - attempt.goal_count)
                        score = attempt.count
                        heapq.heappush(search.frontier, (int(score), attempt))
                        search.seen.add(attempt)

        # if a legal move could not be made print some progress statistics and updated the best game found so far
        if not legalMove:
            search.print(game)
            if game.iou() > search.bestGameFound.iou():
                search.bestGameFound = game
                print("\n...{}\n".format([(i+1, j+1, GameState.dir2str(d)) for i, j, d in game.moves[:game.init_count-game.count]]), end="")

    print("...solution found!" if search.bestGameFound.is_solved() else "...not solved!")
    return search.bestGameFound


if __name__ == "__main__":

    # 45-hole standard game
    if False:
        filename = "pegs45.tex"
        print("writing LaTeX to {} ...".format(filename))
        with open(filename, 'wt') as file:
            file.write(getLaTeXHeader())

            game = prioritySearch()
            file.write("\n\t" + r"\begin{center} {\Huge 45-Hole Peg Solitaire} \end{center}" + "\n")
            file.write(getLaTeXGame(game))
            file.write(getLaTeXFooter())

    # 45-hole single-vacancy games
    if False:
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
                game = prioritySearch(init_state=start, goal_state=goal, maxMoves=10000)
                if game.is_solved():
                    file.write(getLaTeXGame(game))
                else:
                    file.write(r"""\vspace*{\fill}\begin{center}no solution\end{center}\vspace*{\fill}""" + "\n")

            file.write(getLaTeXFooter())

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
                game = prioritySearch(init_state=start, goal_state=goal)
                if game.is_solved():
                    file.write(getLaTeXGame(game))
                else:
                    file.write(r"""\vspace*{\fill}\begin{center}no solution\end{center}\vspace*{\fill}""" + "\n")

            file.write(getLaTeXFooter())

