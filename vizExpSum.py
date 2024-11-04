#!/usr/bin/env python3
# -----------------------------------------------------------------------
# VIZEXPSUM
# -----------------------------------------------------------------------

import math
from calendar import monthrange, month_name

def term(n, day, month, year):
    """Evaluate the n-th term in the sequence."""
    theta = n/month + math.pow(n, 2)/day + math.pow(n,3)/year
    x = math.cos(2.0 * math.pi * theta)
    y = math.sin(2.0 * math.pi * theta)
    return x, y

def sequence(day, month, year, N=None):
    """Evaluate the a sequence of length N."""
    if N is None:
        N = 2 * math.lcm(day, month, year) + 1

    x_points = [1.0 for i in range(N)]
    y_points = [0.0 for i in range(N)]
    for n in range(1, N):
        x, y = term(n, day, month, year)
        x_points[n] = x_points[n-1] + x
        y_points[n] = y_points[n-1] + y

    return x_points, y_points

def sequence2tikz(x_points, y_points, indent=1):
    """Convert a sequence of points to tikz draw command."""
    x_min, x_max = min(x_points), max(x_points)
    y_min, y_max = min(y_points), max(y_points)

    join_str = "\n\t" + ("\t" * indent) + " -- "
    return ("\t" * indent) + "\\draw[black] " + join_str.join(["({:0.3f}, {:0.3f})".format((x - x_min)/(x_max - x_min), (y - y_min)/(y_max - y_min)) for x, y in zip(x_points, y_points)]) + ";\n"


def calendar(filename, month, year, N=None):
    """Produce a LaTeX calendar for the given month."""
    assert (1 <= month <= 12) and (0 <= year <= 99)

    index, days = monthrange(2000 + year, month)

    print("Creating calendar for {} 20{:02} and writing to {}...".format(month_name[month], year, filename))
    with open(filename, 'wt') as file:
        # write header
        file.write("% VIZEXPSUM {}, 20{:02}\n".format(month_name[month], year))
        file.write("% compile with 'pdflatex -shell-escape'\n\n")

        file.write("\\documentclass[10pt,a4paper,landscape]{article}\n\n")
        file.write("\\usepackage{pgfplots}\n")
        file.write("\\usepackage{tikz}\n")
        file.write("\\usepgfplotslibrary{external}\n")
        file.write("\\tikzexternalize\n\n")
        file.write("\\usepackage[cm]{fullpage}\n\n")

        file.write("\\begin{document}\n")
        file.write("\t\\thispagestyle{empty}\n\n")

        # write body
        file.write("\t\\vfill\n")
        file.write("\t\\begin{center}\n")
        file.write("\t\t{{\\Huge {}, 20{:02}}}\n".format(month_name[month], year))
        file.write("\t\t\\vfill\n\n")

        file.write("\t\t\\begin{tabular}{ccccccc}\n\t\t\t")
        file.write("& " * index)
        file.write("\n")

        # draw diagram for each day
        for day in range(days):
            x_points, y_points = sequence(day + 1, month, year, N)
            x_offset = (day + index) % 7
            y_offset = math.floor((day + index) / 7)

            file.write("\t\t\t\\begin{tikzpicture}[scale=2]\n")
            file.write("\t\t\t\t\\clip (-0.1,-0.1) rectangle (1.1,1.1);\n")
            file.write(sequence2tikz(x_points, y_points, 4))
            file.write("\t\t\t\\end{tikzpicture}\n")

            if x_offset == 6:
                file.write("\t\t\t\\\\\n")
            else: file.write("\t\t\t&\n")

        file.write("\t\t\\end{tabular}\n")
        file.write("\t\\end{center}\n")
        file.write("\t\\vfill\n")

        # write footer
        file.write("\\end{document}\n\n")

# --- main ------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    calendar("vizExpSumOct2024.tex", 10, 24)
    calendar("vizExpSumNov2024.tex", 11, 24)
    calendar("vizExpSumDec2024.tex", 12, 24, 200)
