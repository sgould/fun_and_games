# Marble Solitaire
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

    def __init__(self):
        # 2d array representing the board (-1: illegal, 0: empty, 1:marble)
        self.board = np.array([[-1 if ((i < 3) or (i > 5)) and ((j < 3) or (j > 5)) else 1 for j in range(9)] for i in range(9)], dtype=np.int8)
        self.board[4, 4] = 0
        self.count = 44
        self.moves = np.empty((43, 3), dtype=np.int8)

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

    def move(self, i, j, d):
        """Execute a jump from (i,j) in direction d. Returns new GameState if successful. Otherwise None."""
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
        state.moves[44 - self.count] = (i, j, d)

        return state

    def solved(self, anyPosition=True):
        """Returns True if solved and False otherwise."""
        return (self.count == 1) and (anyPosition or (self.board[4, 4] == 1))

    def mst(self):
        """Returns cost of minimum hamming-distance (L1) spanning tree."""
        if self.count <= 1:
            return 0, 0, 0, 0

        marbles = np.transpose(np.nonzero(self.board == 1))
        n = len(marbles)
        dist = [(abs(marbles[i][0] - marbles[j][0]) + abs(marbles[i][1] - marbles[j][1]), i, j) for i in range(1,n) for j in range(i)]
        dist.sort(key=lambda x: x[0])

        diameter = dist[-1][0]
        area = np.prod(np.max(marbles, axis=0) - np.min(marbles, axis=0) + 1)

        visited = np.zeros((9,9))

        # add first edge
        c, i, j = dist.pop(0)
        totalCost, lastCost = c, c
        visited[marbles[i][0], marbles[i][1]] = 1
        visited[marbles[j][0], marbles[j][1]] = 1

        # add remaining edges
        for ni in range(n-2):
            bFound = False
            for c, i, j in dist:
                #if (visited[marbles[i][0], marbles[i][1]] == 1) and (visited[marbles[j][0], marbles[j][1]] == 1):
                #    continue
                if visited[marbles[i][0], marbles[i][1]] != visited[marbles[j][0], marbles[j][1]]:
                    totalCost += c
                    lastCost = c
                    visited[marbles[i][0], marbles[i][1]] = 1
                    visited[marbles[j][0], marbles[j][1]] = 1
                    bFound = True
                    break
            assert bFound

        return totalCost, lastCost, diameter, area

    def __eq__(self, other):
        if (self.count != other.count):
            return False
        if np.array_equal(self.board, other.board):
            return True
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
        return "\n".join(["".join(["O" if self.board[i, j] == 1 else "." if self.board[i, j] == 0 else " " for j in range(9)]) for i in range(9)])

    def __hash__(self):
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
        print("\rtried {} moves, skipped {} moves, {} marbles remaining, {} games in frontier, {}/{} smallest/biggest game in frontier".format(
                self.movesEvaluated, self.movesSkipped, game.count if game else 45, len(self.frontier),
            min([g.count for (s, g) in self.frontier]), max([g.count for (s, g) in self.frontier])), end="")


def gameMoves2Latex(game):
    """Prints the history of game moves as LaTeX/TikZ source."""

    out_str = r"""
    \newcommand{\drawboard}[1]{ % 2d board array (-1: illegal, 0: empty, 1: occupied, 2: src, 3: dst)
        \draw[black, thick, fill=black!10] (5, 5) circle (5cm);
        \foreach \x in {1,2,...,9}{
            \foreach \y in {1,2,...,9}{
                \pgfmathsetmacro{\value}{int(#1[9-\y][\x-1])}
                \pgfmathparse{\value == 0}\ifdim\pgfmathresult pt>0pt\draw[black!50, fill=black!10] (\x, \y) circle (4mm);\fi
                \pgfmathparse{\value == 1}\ifdim\pgfmathresult pt>0pt\shade[ball color=blue!50] (\x, \y) circle (4mm);\fi
                \pgfmathparse{\value == 2}\ifdim\pgfmathresult pt>0pt\shade[ball color=red!50] (\x, \y) circle (4mm);\fi
                \pgfmathparse{\value == 3}\ifdim\pgfmathresult pt>0pt\draw[red!50, fill=black!10] (\x, \y) circle (4mm);\fi
            }
        }
    }
    
    \begin{center}
	    \begin{tikzpicture}[scale=0.25]
    """

    g = GameState()
    count = 0
    for i, j, d in game.moves[:44 - game.count]:
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
    print("started at {}...".format(time.asctime()))

    search = SearchState()
    game = GameState()
    heapq.heappush(search.frontier, (0, game))
    search.seen.add(game)
    search.bestGameFound = game

    while (len(search.frontier)):
        search.movesEvaluated += 1
        score, game = heapq.heappop(search.frontier)

        if game.solved(False):
            search.bestGameFound = game
            search.print()
            print("\n...{}\n".format([(i + 1, j + 1, GameState.dir2str(d)) for i, j, d in game.moves]), end="")
            break
        if (maxMoves is not None) and (search.movesEvaluated >= maxMoves):
            break

        legalMove = False
        for i, j in zip(*np.nonzero(game.board == 1)):
            for d in range(4):
                attempt = game.move(i, j, d)
                if attempt is not None:
                    if attempt in search.seen:
                        search.movesSkipped += 1
                    else:
                        totalCost, lastCost, diameter, area = attempt.mst()

                        # check solveable heuristics
                        if totalCost >= 2 * attempt.count:
                            search.movesSkipped += 1
                        elif lastCost >= 5:
                            search.movesSkipped += 1
                        else:
                            legalMove = True
                            #score = attempt.count
                            #score = 10 * attempt.count + lastCost
                            score = area - attempt.count
                            heapq.heappush(search.frontier, (int(score), attempt))
                            search.seen.add(attempt)

        if not legalMove:
            search.print(game)
            if game.count < search.bestGameFound.count:
                search.bestGameFound = game
                print("\n...{}\n".format([(i+1, j+1, GameState.dir2str(d)) for i, j, d in game.moves[:44-game.count]]), end="")

    return search.bestGameFound


if __name__ == "__main__":
    game = prioritySearch()
    print(gameMoves2Latex(game))

