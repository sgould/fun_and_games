# PEG SWAP PUZZLE
# Stephen Gould
#
# There are many variants of peg puzzles. In this one, the goal is to swap the positions of the red and black pegs. Red
# pegs can only move right, and black pegs can only move left. A peg can move into an adjacent hole if it is empty. Pegs
# can also jump a single different-coloured peg to move into an empty hole.
#
# There are over 19M solutions (excluding first-move symmetries) ranging from 46 moves to 58 moves. This code finds an
# example of each.
#
#           3               11
#       1       6       9       14
#   0       4       8       12      16
#       2       7       10      15
#           5               13
#

import copy
import numpy as np

RED = 1
BLACK = -1
EMPTY = 0

EDGES = ((0, 1), (0, 2), (1, 3), (1, 4), (2, 4), (2, 5), (3, 6), (4, 6), (4, 7), (5, 7), (6, 8), (7, 8),
         (8, 9), (8, 10), (9, 11), (9, 12), (10, 12), (10, 13), (11, 14), (12, 14), (12, 15), (13, 15), (14, 16), (15, 16))

JUMPS = ((0, 1, 3), (0, 2, 5), (1, 4, 7), (2, 4, 6), (3, 6, 8), (5, 7, 8),
         (6, 8, 10), (7, 8, 9),
         (8, 9, 11), (8, 10, 13), (9, 12, 15), (10, 12, 14), (11, 14, 16), (13, 15, 16))

EDGES_R = [() for i in range(17)]
EDGES_B = [() for i in range(17)]
JUMPS_R = [() for i in range(17)]
JUMPS_B = [() for i in range(17)]

for i in range(17):
    EDGES_R[i] = tuple(m for m in EDGES if m[1] == i)
    EDGES_B[i] = tuple(m for m in EDGES if m[0] == i)
    JUMPS_R[i] = tuple(m for m in JUMPS if m[2] == i)
    JUMPS_B[i] = tuple(m for m in JUMPS if m[0] == i)

TARGET = np.zeros((17,), dtype=np.int8)
TARGET[:8] = BLACK
TARGET[9:] = RED

class GameState:
    """State of the board and update functions."""

    def __init__(self):
        self.board = np.zeros((17,), dtype=np.int8)
        self.board[:8] = RED
        self.board[9:] = BLACK
        self.free_peg = 8

        self.num_moves = 0
        self.prev_state = None

    def move(self, src, dst):
        """Move a peg."""
        assert self.board[dst] == EMPTY
        new_state = copy.copy(self)
        new_state.board = copy.deepcopy(self.board)
        new_state.board[dst] = self.board[src]
        new_state.board[src] = EMPTY
        new_state.free_peg = src
        new_state.num_moves += 1
        new_state.prev_state = self
        return new_state

    def is_solved(self):
        """Returns True if solved and False otherwise."""
        return np.array_equal(self.board, TARGET)

    def history(self):
        """Return trace of moves."""
        trace = [self.board]
        moves = [(self.free_peg, self.free_peg)]
        game = self.prev_state
        while (game is not None):
            trace.insert(0, game.board)
            moves.insert(0, (moves[0][1], game.free_peg))
            game = game.prev_state
        return trace, moves

    @staticmethod
    def peg2str(p):
        if p == RED:
            return " R"
        if p == BLACK:
            return " B"
        return " -"

    @staticmethod
    def board2str(b):
        pegs = [GameState.peg2str(b[i]) for i in range(17)]
        str = ""
        str += "    {}      {}\n".format(pegs[3], pegs[11])
        str += "  {}  {}  {}  {}\n".format(pegs[1], pegs[6], pegs[9], pegs[14])
        str += "{}  {}  {}  {}  {}\n".format(pegs[0], pegs[4], pegs[8], pegs[12], pegs[16])
        str += "  {}  {}  {}  {}\n".format(pegs[2], pegs[7], pegs[10], pegs[15])
        str += "    {}      {}\n".format(pegs[5], pegs[13])
        return str

    def __str__(self):
        return GameState.board2str(self.board)

# ----------------------------------------------------------------------------

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

        \def\px{{0, 1, 1, 2, 2, 2, 3, 3, 4, 5, 5, 6, 6, 6, 7, 7, 8}}
		\def\py{{2, 3, 1, 4, 2, 0, 3, 1, 2, 3, 1, 4, 2, 0, 3, 1, 2}}
        \newcommand{\drawboard}[3]{ % 17-dimensional board array (-1: black, 0: empty, 1: red), source, target
            \draw [draw=black!50] (-1,-1) rectangle (9,5);
            \foreach \i in {0,1,...,16}{
            	\node[minimum size=1.75mm, inner sep=0pt, circle] (\i) at (\px[\i], \py[\i]) {};
                \pgfmathsetmacro{\value}{int(#1[\i])}
                \pgfmathparse{\value == -1}\ifdim\pgfmathresult pt>0pt\draw[thin, black!50, fill=black!50] (\i) circle (3.5mm);\fi
                \pgfmathparse{\value == 0}\ifdim\pgfmathresult pt>0pt\draw[thin, black!50, fill=black!10] (\i) circle (3.5mm);\fi
                \pgfmathparse{\value == 1}\ifdim\pgfmathresult pt>0pt\draw[thin, red!50, fill=red!50] (\i) circle (3.5mm);\fi
            }
			\ifthenelse{\equal{#2}{#3}}{}{\draw (#2) to[bend right=45] (#3)};
        }

    """


def getLaTeXFooter():
    """Returns footer for LaTeX/TikZ source."""
    return r"\end{document}"


def getLaTeXGame(game):
    """Returns the game moves as LaTeX/TikZ source."""

    out_str = r"""
        \vspace*{\fill}
        \begin{center}
            \begin{tikzpicture}[scale=0.25]
    """

    boards, moves = game.history()
    for i in range(len(boards)):
        board_string = r"{" + ", ".join([str(boards[i][j]) for j in range(17)]) + r"}"

        out_str += "\t\\begin{{scope}}[xshift={}cm, yshift={}cm]\n".format(12*(i % 5), -8 * int(i / 5))
        out_str += "\t\t\\drawboard{" + board_string + "}}{{{}}}{{{}}};\n".format(moves[i][0], moves[i][1])
        out_str += "\t\\end{scope}\n"

    out_str += r"""
            \end{tikzpicture}
        \end{center}
        \vspace*{\fill}    
    """

    return out_str


# ----------------------------------------------------------------------------

if __name__ == "__main__":

    # initialise search
    frontier = [GameState()]
    numStatesExplored = 0
    solutions = {}
    numSolutionsFound = 0
    bestSolutionFound = None
    bestSolutionMoves = np.inf

    # force first three moves
    if True:
        frontier[0] = frontier[0].move(10, 8)
        frontier[0] = frontier[0].move(6, 10)
        frontier[0] = frontier[0].move(8, 6)

    # search for best solution
    while (len(frontier)):
        state = frontier.pop()
        numStatesExplored += 1
        if numStatesExplored % 5000 == 0:
            print("\r...{} ({}, {})".format(numStatesExplored, numSolutionsFound, len(frontier)), end="")

        if state.is_solved():
            numSolutionsFound += 1
            if state.num_moves < bestSolutionMoves:
                bestSolutionFound = state
                bestSolutionMoves = state.num_moves
            if state.num_moves not in solutions:
                solutions[state.num_moves] = state
                print("\r...{} ({}, {})".format(numStatesExplored, numSolutionsFound, len(frontier)), end="")
                print("\nsolution found with {} moves".format(state.num_moves))

            #if state.num_moves == 46:
            #    break
            continue

        """
        for u, v in EDGES:
            if (state.board[u] == RED) and (state.board[v] == EMPTY):
                frontier.append(state.move(u, v))

            if (state.board[u] == EMPTY) and (state.board[v] == BLACK):
                frontier.append(state.move(v, u))

        for u, v, w in JUMPS:
            if (state.board[u] == RED) and (state.board[v] == BLACK) and (state.board[w] == EMPTY):
                frontier.append(state.move(u, w))

            if (state.board[u] == EMPTY) and (state.board[v] == RED) and (state.board[w] == BLACK):
                frontier.append(state.move(w, u))
        """

        for u, v in EDGES_R[state.free_peg]:
            if (state.board[u] == RED):
                frontier.append(state.move(u, v))

        for u, v in EDGES_B[state.free_peg]:
            if (state.board[v] == BLACK):
                frontier.append(state.move(v, u))

        for u, v, w in JUMPS_R[state.free_peg]:
            if (state.board[u] == RED) and (state.board[v] == BLACK):
                frontier.append(state.move(u, w))

        for u, v, w in JUMPS_B[state.free_peg]:
            if (state.board[v] == RED) and (state.board[w] == BLACK):
                frontier.append(state.move(w, u))

    # print out the best solution found
    assert bestSolutionFound is not None
    print("\n")
    boards, moves = bestSolutionFound.history()
    print("\n".join(GameState.board2str(b) for b in boards))

    # print out statistics
    print("{} states explored".format(numStatesExplored))
    print("{} solutions found".format(numSolutionsFound))
    print("{} moves in best solution".format(bestSolutionMoves))

    # write out LaTeX of solutions
    filename = "peg_swap.tex"
    print("writing LaTeX to {} ...".format(filename))
    with open(filename, 'wt') as file:
        file.write(getLaTeXHeader())
        for numMoves in reversed(sorted(solutions.keys())):
            file.write("\n\t" + r"\begin{center} {\Huge " + str(numMoves) + r"-Move Solution} \end{center}" + "\n")
            file.write(getLaTeXGame(solutions[numMoves]))
            file.write("\n\t\t" + r"\newpage" + "\n")
        file.write(getLaTeXFooter())
