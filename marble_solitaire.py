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

    def __init__(self):
        # 2d array representing the board (-1: illegal, 0: empty, 1:marble)
        self.board = np.array([[-1 if ((i < 3) or (i > 5)) and ((j < 3) or (j > 5)) else 1 for j in range(9)] for i in range(9)], dtype=np.int8)
        self.board[4, 4] = 0
        self.count = 44
        self.moves = []

    def move(self, i, j, d):
        """Execute a jump from (i,j) in direction d. Returns new GameState if successful. Otherwise None."""
        #assert (0 <= i < 9) and (0 <= j < 9) and (0 <= d < 4)

        # check that position contains a marble
        if self.board[i, j] != 1:
            return None

        if d == 0:
            if (i >= 7): return None
            if (self.board[i + 1, j] != 1): return None
            if (self.board[i + 2, j] != 0): return None
            di, dj = 1, 0
            dstr = "down"
        elif d == 1:
            if (j >= 7): return None
            if (self.board[i, j + 1] != 1): return None
            if (self.board[i, j + 2] != 0): return None
            di, dj = 0, 1
            dstr = "right"
        elif d == 2:
            if (i < 2): return None
            if (self.board[i - 1, j] != 1): return None
            if (self.board[i - 2, j] != 0): return None
            di, dj = -1, 0
            dstr = "up"
        else:
            if (self.board[i, j - 1] != 1): return None
            if (self.board[i, j - 2] != 0): return None
            if (j < 2): return None
            di, dj = 0, -1
            dstr = "left"

        # check move stays within board
        #if not (0 <= i + 2 * di < 9) or not (0 <= j + 2 * dj < 9):
        #    assert None

        # check that there exists a marble to jump and that the destination is empty
        #if (self.board[i + di, j + dj] != 1) or (self.board[i + 2 * di, j + 2 * dj] != 0):
        #   return None

        # make the move
        state = copy.deepcopy(self)
        state.board[i, j] = 0
        state.board[i + di, j + dj] = 0
        state.board[i + 2 * di, j + 2 * dj] = 1
        state.count = self.count - 1
        state.moves.append((i+1, j+1, dstr))

        return state

    def solved(self, anyPosition=True):
        """Returns True if solved and False otherwise."""
        return (self.count == 1) and (anyPosition or (self.board[4, 4] == 1))

    def coords(self):
        """Returns coordinates of remaining marbles."""
        return tuple((i, j) for i in range(9) for j in range(9) if self.board[i, j] == 1)

    def mst(self):
        """Returns cost of minimum hamming-distance (L1) spanning tree."""
        if self.count <= 1:
            return 0

        marbles = self.coords()
        n = len(marbles)
        dist = [(abs(marbles[i][0] - marbles[j][0]) + abs(marbles[i][1] - marbles[j][1]), i, j) for i in range(1,n) for j in range(i)]
        dist.sort(key=lambda x: x[0])

        #diameter = dist[-1][0]
        visited = np.zeros((9,9))

        # add first edge
        c, i, j = dist.pop(0)
        cost = c
        visited[marbles[i][0], marbles[i][1]] = 1
        visited[marbles[j][0], marbles[j][1]] = 1

        # add remaining edges
        for ni in range(n-2):
            bFound = False
            for c, i, j in dist:
                if (visited[marbles[i][0], marbles[i][1]] == 1) and (visited[marbles[j][0], marbles[j][1]] == 1):
                    continue
                if visited[marbles[i][0], marbles[i][1]] != visited[marbles[j][0], marbles[j][1]]:
                    cost += c
                    visited[marbles[i][0], marbles[i][1]] = 1
                    visited[marbles[j][0], marbles[j][1]] = 1
                    bFound = True
                    break
            assert bFound

        return cost

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
        return int(sum([pow(2, abs(i - 4) + abs(j - 4)) for i in range(9) for j in range(9) if self.board[i, j] == 1]))


def prioritySearch(maxMoves=None):
    print("started at {}...".format(time.asctime()))
    bestFound = 45
    movesEvaluated = 0
    movesSkipped = 0
    frontier = []
    game = GameState()
    heapq.heappush(frontier, (game.mst(), game))
    seen = set()

    while (len(frontier)):
        movesEvaluated += 1
        score, game = heapq.heappop(frontier)

        if game.solved():
            print("\rtried {} moves, skipped {} moves, {} marbles remaining, {} games in frontier".format(movesEvaluated, movesSkipped, game.count, len(frontier)), end="")
            break
        if (maxMoves is not None) and (movesEvaluated >= maxMoves):
            break

        seen.add(game)
        legalMove = False
        for i in range(9):
            for j in range(9):
                if game.board[i, j] != 1:
                    continue
                for d in range(4):
                    attempt = game.move(i, j, d)
                    if attempt is not None:
                        #legalMove = True
                        if attempt in seen:
                            movesSkipped += 1
                        else:
                            seen.add(attempt)
                            cost = attempt.mst()

                            # check solveable heuristic
                            if cost >= 2 * attempt.count:
                                movesSkipped += 1
                            else:
                                legalMove = True
                                #score = cost * cost / attempt.count
                                #score = 2 * attempt.count - cost
                                score = attempt.count
                                heapq.heappush(frontier, (score, attempt))

        if legalMove is False:
            print("\rtried {} moves, skipped {} moves, {} marbles remaining, {} games in frontier".format(movesEvaluated, movesSkipped, game.count, len(frontier)), end="")
            if game.count < bestFound:
                bestFound = game.count
                print("\n...{}\n".format(game.moves), end="")


if __name__ == "__main__":
    prioritySearch()
    exit(0)

    import cProfile, pstats, io
    from pstats import SortKey

    pr = cProfile.Profile()
    pr.enable()
    prioritySearch(2000)
    pr.disable()
    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())
