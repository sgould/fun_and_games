# FINDAWORD: Generates find-a-word puzzles
# by Bronte Gould and Stephen Gould

from math import sqrt
from random import shuffle, sample

words = ["dog", "cat", "bird", "fish", "elephant", "mouse", "tiger", "lion", "snail", "rabbit", "frog", "chicken",
         "snake", "emu", "kangaroo", "rhino", "wombat", "cow", "horse", "sheep", "goat", "pig", "deer", "monkey",
         "koala", "bear", "giraffe", "butterfly", "camel", "dolphin", "duck", "turtle"]

words = [w.upper() for w in words]
words = sorted(words, key=lambda w: len(w), reverse=True)
letters = sum([len(w) for w in words])

size = int(max(2 * len(words[0]), sqrt(0.5 * letters)))
grid = [['.' for i in range(size)] for j in range(size)]


def format_puzzle(grid):
    """Formats the puzzle for printing."""
    puzzle = ""
    for line in grid:
        puzzle += " ".join(line) + "\n"
    return puzzle


def check_placement(word, grid, location, direction):
    """
    Checks if a word fits at the specified location and returns the number of letters overlapping with already-placed
    words. If the word cannot fit (e.g., conflicts with already-placed letters) then returns -1.

    :param word: The word to place.
    :param grid: Current state of the (partially) filled puzzle.
    :param location: Starting location for the word (row, column).
    :param direction: Direction to increment letters of the word (e.g., (0, 1)).
    :return: Number of overlaps with existing letters or -1 if cannot be placed.
    """

    assert -1 <= direction[0] <= 1
    assert -1 <= direction[1] <= 1

    # get size of puzzle
    H, W = len(grid), len(grid[0])

    # loop of each letter in the word
    overlaps = 0
    location = list(location)
    for i in range(len(word)):
        # check that the word fits into the puzzle grid
        if (location[0] < 0) or (location[1] < 0) or (location[0] >= H) or (location[1] >= W):
            return -1

        # check that the location is empty or already contains the same letter
        if (grid[location[0]][location[1]] != '.') and (grid[location[0]][location[1]] != word[i]):
            return -1

        # count overlapping letters
        if (grid[location[0]][location[1]] == word[i]):
            overlaps += 1

        # update location
        location[0] += direction[0]
        location[1] += direction[1]

    return overlaps


def place_word(word, grid, overlap=0):
    """Places a word into the puzzle overlapping by overlap with already-placed letters."""

    rows = list(range(len(grid)))
    cols = list(range(len(grid[0])))
    dirs = [(1, 0), (0, 1), (1, 1), (-1, 0), (0, -1), (-1, -1)]

    shuffle(rows)
    for i in rows:
        shuffle(cols)
        for j in cols:
            shuffle(dirs)
            for d in dirs:
                if check_placement(word, grid, (i, j), d) >= overlap:
                    for k in range(len(word)):
                        grid[i + k * d[0]][j + k * d[1]] = word[k]
                    return True

    return False


def fill_random_letters(grid):
    """Fills empty grid locations with a random letter."""

    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if grid[i][j] == '.':
                grid[i][j] = sample("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 1)[0]


for word in words:
    if not place_word(word, grid, 2):
        if not place_word(word, grid, 1):
            if not place_word(word, grid):
                print("Could not place word {}".format(word))
                exit(-1)

print(format_puzzle(grid))
print("\n")
fill_random_letters(grid)
print(format_puzzle(grid))

print("Word list ({}):".format(len(words)))
for w in words:
    print("\t{}".format(w))
