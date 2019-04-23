#!/usr/bin/env python
#
# Examples of model overfitting for 1d regression problem to be used in introductory lectures on machine learning.
#

import numpy as np
import numpy.random as rnd
from sklearn import linear_model
import matplotlib.pyplot as plt


# generate data for the examples
x = np.linspace(0.0, 1.0, num=100)
y = 3.0 ** x ** 5 - 2.0 * x ** 4 - x**3 + 0.5 * x ** 2 + x

rnd.seed(0)
indx = rnd.permutation(range(len(x)))
i_trn = indx[0:10]
i_tst = indx[11:20]

print(i_trn)
print(i_tst)


# model selection
def fit_and_plot(x, y, phi, i_trn, title):
    """Fit model and plot resulting curve."""

    model = linear_model.LinearRegression()
    model.fit(phi[i_trn], y[i_trn])

    plt.plot(x, model.predict(phi), 'r--', lw=2)
    plt.plot(x[i_trn], y[i_trn], 'bo', markersize=12, markeredgewidth=0)
    plt.title(title); plt.xlabel(r"$x$"); plt.ylabel(r"$y$"); plt.grid(True)
    plt.gca().set_yticklabels([]); plt.gca().set_xticklabels([])


plt.figure()
plt.subplot(2, 2, 1)
plt.plot(x[i_trn], y[i_trn], 'bo', markersize=12, markeredgewidth=0)
plt.title("data"); plt.xlabel(r"$x$"); plt.ylabel(r"$y$"); plt.grid(True)
plt.gca().set_yticklabels([]); plt.gca().set_xticklabels([])

plt.subplot(2, 2, 2)
phi = x.reshape(-1, 1)
fit_and_plot(x, y, phi, i_trn, r"$\phi(x) = (x, 1)$")

plt.subplot(2, 2, 3)
phi = np.array([[xi, xi**2] for xi in x])
fit_and_plot(x, y, phi, i_trn, r"$\phi(x) = (x, x^2, 1)$")

plt.subplot(2, 2, 4)
phi = np.array([[xi, xi**2, xi**3, xi**4, xi**5] for xi in x])
fit_and_plot(x, y, phi, i_trn, r"$\phi(x) = (x, x^2, x^3, x^4, x^5, 1)$")

plt.show()


# regularization
model = linear_model.Ridge(alpha=0.1)


# sampling (train/test splits)