#!/usr/bin/env python
#
# Examples of model overfitting for 1d regression problem to be used in introductory lectures on machine learning.
#

import numpy as np
import numpy.random as rnd
from sklearn import linear_model
import matplotlib.pyplot as plt


# generate data for the examples
rnd.seed(1)

x = np.linspace(0.0, 1.0, num=100)
y_true = 3.0 ** x ** 5 - 2.0 * x ** 4 - x**3 + 0.5 * x ** 2 + x
y = y_true + rnd.normal(0.0, 1.0e-3, x.shape)

indx = rnd.permutation(range(len(x)))
i_trn = indx[0:10]
i_tst = indx[11:20]

def fit_and_plot(x, y, phi, i_trn, model, title):
    """Fit model and plot resulting curve."""

    if model is not None:
        model.fit(phi[i_trn], y[i_trn])
        plt.plot(x, model.predict(phi), 'r--', lw=2)

    #plt.plot(x, y, 'b--', lw=1)
    plt.plot(x[i_trn], y[i_trn], 'bo', markersize=12, markeredgewidth=0)
    #plt.xlabel(r"$x$"); plt.ylabel(r"$y$")
    plt.title(title); plt.grid(True)
    plt.gca().set_yticklabels([]); plt.gca().set_xticklabels([])


# model selection
plt.figure()
plt.subplot(2, 2, 1)
fit_and_plot(x, y, [], i_trn, None, "data")

plt.subplot(2, 2, 2)
phi = x.reshape(-1, 1)
fit_and_plot(x, y, phi, i_trn, linear_model.LinearRegression(), r"$\phi(x) = (x, 1)$")

plt.subplot(2, 2, 3)
phi = np.array([[xi, xi**2] for xi in x])
fit_and_plot(x, y, phi, i_trn, linear_model.LinearRegression(), r"$\phi(x) = (x, x^2, 1)$")

plt.subplot(2, 2, 4)
phi = np.array([[xi, xi**2, xi**3, xi**4, xi**5] for xi in x])
fit_and_plot(x, y, phi, i_trn, linear_model.LinearRegression(), r"$\phi(x) = (x, x^2, x^3, x^4, x^5, 1)$")

# regularization
plt.figure()
plt.subplot(2, 2, 1)
fit_and_plot(x, y, [], i_trn, None, "data")

plt.subplot(2, 2, 2)
phi = np.array([[xi, xi**2, xi**3, xi**4, xi**5] for xi in x])
fit_and_plot(x, y, phi, i_trn, linear_model.Ridge(alpha=0.0), r"$\lambda = 0$")

plt.subplot(2, 2, 3)
fit_and_plot(x, y, phi, i_trn, linear_model.Ridge(alpha=1.0e-6), r"$\lambda = 10^{-6}$")

plt.subplot(2, 2, 4)
fit_and_plot(x, y, phi, i_trn, linear_model.Ridge(alpha=0.01), r"$\lambda = 10^{-2}$")

# sampling (train/test splits)
plt.figure()


plt.show()
