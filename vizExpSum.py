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


def sequence2pstricks(x_points, y_points, indent=1):
    """Convert a sequence of points to pstricks command."""
    x_min, x_max = min(x_points), max(x_points)
    y_min, y_max = min(y_points), max(y_points)

    join_str = ""
    cmd_str = ("\t" * indent) + "\\psline"
    out_str = ""
    for start_indx in range(0, len(x_points), 100):
        end_indx = min(start_indx + 101, len(x_points))
        out_str += cmd_str
        out_str += join_str.join(["({:d},{:d})".format(int(1000*(x - x_min)/(x_max - x_min)),
                                                       int(1000*(y - y_min)/(y_max - y_min))) for x, y in zip(x_points[start_indx:end_indx], y_points[start_indx:end_indx])]) + "\n"

    return out_str
    #return ("\t" * indent) + "\\psline" + join_str.join(["({:d},{:d})".format(int(1000*(x - x_min)/(x_max - x_min)), int(1000*(y - y_min)/(y_max - y_min))) for x, y in zip(x_points, y_points)]) + "\n"


def calendar(filename, month, year, method='tikz'):
    """Produce a LaTeX calendar for the given month."""
    assert (1 <= month <= 12)
    assert method in ('tikz', 'pstricks')

    index, days = monthrange(year, month)

    print("Creating calendar for {} {} and writing to {}...".format(month_name[month], year, filename))
    with open(filename, 'wt') as file:
        # write header
        file.write("% VIZEXPSUM {}, {}\n".format(month_name[month], year))
        file.write("% compile with 'pdflatex -shell-escape {}'\n\n".format(filename))

        file.write("\\documentclass[10pt,a4paper,landscape]{article}\n\n")

        if method == 'tikz':
            file.write("\\usepackage{pgfplots}\n")
            file.write("\\usepackage{tikz}\n")
            file.write("\\usepgfplotslibrary{external}\n")
            file.write("\\tikzexternalize\n")

        if method == 'pstricks':
            file.write("\\usepackage[pdf]{pstricks}\n")
            file.write("\\usepackage{auto-pst-pdf}\n")
            file.write("\\psset{unit=0.025mm, linewidth=0.1pt}\n")

        file.write("\n")
        file.write("\\usepackage[cm]{fullpage}\n\n")

        file.write("\\begin{document}\n")
        file.write("\t\\thispagestyle{empty}\n\n")

        # write body
        file.write("\t\\vfill\n")
        file.write("\t\\begin{center}\n")
        file.write("\t\t{{\\Huge {}, {}}}\n".format(month_name[month], year))
        file.write("\t\t\\vfill\n\n")

        file.write("\t\t\\begin{tabular}{ccccccc}\n\t\t\t")
        file.write("& " * index)
        file.write("\n")

        # draw diagram for each day
        for day in range(days):
            x_points, y_points = sequence(day + 1, month, year % 100)
            x_offset = (day + index) % 7
            y_offset = math.floor((day + index) / 7)

            if method == 'tikz':
                file.write("\t\t\t\\begin{tikzpicture}[scale=2]\n")
                file.write("\t\t\t\t\\clip (-0.1,-0.1) rectangle (1.1,1.1);\n")
                file.write(sequence2tikz(x_points, y_points, 4))
                file.write("\t\t\t\\end{tikzpicture}\n")

            if method == 'pstricks':
                file.write("\t\t\t\\begin{pspicture}(-100,-100)(1100,1100)\n")
                file.write(sequence2pstricks(x_points, y_points, 4))
                file.write("\t\t\t\\end{pspicture}\n")

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
    # TODO: add command line options to input month/year and optionally invoke pdflatex
    #calendar("vizExpSumOct2024.tex", 10, 2024)
    calendar("vizExpSumNov2024.tex", 11, 2024, 'pstricks')
    #calendar("vizExpSumDec2024.tex", 12, 2024)
    #calendar("vizExpSumJan2025.tex", 1, 2025)
    calendar("vizExpSumNov1973.tex", 11, 1973, 'pstricks')

