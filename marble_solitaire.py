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

    hash_indx = np.array([[0, 0, 0, 65536, 16384, 65536, 0, 0, 0], [0, 0, 0, 2048, 512, 2048, 0, 0, 0], [0, 0, 0, 64, 16, 64, 0, 0, 0],
                          [65536, 2048, 64, 4, 1, 4, 64, 2048, 65536], [16384, 512, 16, 1, 0, 1, 16, 512, 16384], [65536, 2048, 64, 4, 1, 4, 64, 2048, 65536],
                          [0, 0, 0, 64, 16, 64, 0, 0, 0], [0, 0, 0, 2048, 512, 2048, 0, 0, 0], [0, 0, 0, 65536, 16384, 65536, 0, 0, 0]], dtype=int)

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
        elif d == 1:
            if (j >= 7): return None
            if (self.board[i, j + 1] != 1): return None
            if (self.board[i, j + 2] != 0): return None
            di, dj = 0, 1
        elif d == 2:
            if (i < 2): return None
            if (self.board[i - 1, j] != 1): return None
            if (self.board[i - 2, j] != 0): return None
            di, dj = -1, 0
        else:
            if (self.board[i, j - 1] != 1): return None
            if (self.board[i, j - 2] != 0): return None
            if (j < 2): return None
            di, dj = 0, -1

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
        state.moves[44 - self.count] = (i, j, d)

        return state

    def unmove(self, i, j, d):
        """Undo a from jump (i,j) in direction d. Useful for building an endgame book.
        Returns new GameState if successful else None."""
        #assert (0 <= i < 9) and (0 <= j < 9) and (0 <= d < 4)

        # check that position is empty (i.e., used to contain a marble)
        if self.board[i, j] != 0:
            return None

        if d == 0:
            if (i >= 7): return None
            if (self.board[i + 1, j] != 0): return None
            if (self.board[i + 2, j] != 1): return None
            di, dj = 1, 0
        elif d == 1:
            if (j >= 7): return None
            if (self.board[i, j + 1] != 0): return None
            if (self.board[i, j + 2] != 1): return None
            di, dj = 0, 1
        elif d == 2:
            if (i < 2): return None
            if (self.board[i - 1, j] != 0): return None
            if (self.board[i - 2, j] != 1): return None
            di, dj = -1, 0
        else:
            if (self.board[i, j - 1] != 0): return None
            if (self.board[i, j - 2] != 1): return None
            if (j < 2): return None
            di, dj = 0, -1

        # check move stays within board
        #if not (0 <= i + 2 * di < 9) or not (0 <= j + 2 * dj < 9):
        #    assert None

        # check that there exists an empty space to jump and that the destination has a marble
        #if (self.board[i + di, j + dj] != 0) or (self.board[i + 2 * di, j + 2 * dj] != 1):
        #   return None

        # make the move
        state = copy.deepcopy(self)
        state.board[i, j] = 1
        state.board[i + di, j + dj] = 1
        state.board[i + 2 * di, j + 2 * dj] = 0
        state.count = self.count + 1
        state.moves[self.count - 1] = (i, j, d)

        return state

    def solved(self, anyPosition=True):
        """Returns True if solved and False otherwise."""
        return (self.count == 1) and (anyPosition or (self.board[4, 4] == 1))

    def mst(self):
        """Returns cost of minimum hamming-distance (L1) spanning tree."""
        if self.count <= 1:
            return 0

        marbles = np.transpose(np.nonzero(self.board == 1))
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
                #if (visited[marbles[i][0], marbles[i][1]] == 1) and (visited[marbles[j][0], marbles[j][1]] == 1):
                #    continue
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
        return int(np.sum(np.where(self.board == 1, GameState.hash_indx, 0)))
        #return int(sum([pow((i - 4) * (i - 4) + (j - 4) * (j - 4), 2) for i, j in zip(*np.nonzero(self.board == 1))]))
        #return int(sum([pow(2, abs(i - 4) + abs(j - 4)) for i, j in zip(*np.where(self.board == 1))]))


def prioritySearch(maxMoves=None):
    print("started at {}...".format(time.asctime()))
    bestFound = 45
    movesEvaluated = 0
    movesSkipped = 0
    frontier = []
    game = GameState()
    heapq.heappush(frontier, (0, game))
    seen = set() # insert when added to frontier
    seen.add(game)

    while (len(frontier)):
        movesEvaluated += 1
        score, game = heapq.heappop(frontier)

        if game.solved():
            print("\rtried {} moves, skipped {} moves, {} marbles remaining, {} games in frontier".format(movesEvaluated, movesSkipped, game.count, len(frontier)), end="")
            print("\n...{}\n".format([(i + 1, j + 1, GameState.dir2str(d)) for i, j, d in game.moves]), end="")
            break
        if (maxMoves is not None) and (movesEvaluated >= maxMoves):
            break

        legalMove = False
        for i, j in zip(*np.nonzero(game.board == 1)):
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

        if not legalMove:
            print("\rtried {} moves, skipped {} moves, {} marbles remaining, {} games in frontier".format(movesEvaluated, movesSkipped, game.count, len(frontier)), end="")
            if game.count < bestFound:
                bestFound = game.count
                print("\n...{}\n".format([(i+1, j+1, GameState.dir2str(d)) for i, j, d in game.moves[:44-game.count]]), end="")



if __name__ == "__main__":
    prioritySearch()
    exit(0)

    import cProfile, pstats, io
    from pstats import SortKey

    pr = cProfile.Profile()
    pr.enable()
    prioritySearch(5000)
    pr.disable()
    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())
