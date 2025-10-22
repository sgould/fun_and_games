# ANIMATION TO ILLUSTRATE NEURAL COLLAPSE
# Stephen Gould <stephen.gould@anu.edu.au>
#

import numpy as np
import matplotlib.pyplot as plt
import cv2


N, K, D = 100, 3, 2
COLOURS = ('b', 'r', 'g', 'm')
MARKERS = ('o', '^', 'd', 's')
#VID_FILENAME = "neural_collapse.mp4"
VID_FILENAME = None


def visualize_state(X_init, X_curr, A_curr, loss_curve, fig=None):
    """Visualize classifier state."""

    if fig is None:
        fig = plt.figure(figsize=(16, 9), dpi=150 if VID_FILENAME else 75)
        fig.tight_layout(pad=0)

    plt.subplot(1, 2, 1)
    plt.gca().clear()
    A_curr = A_curr / np.linalg.norm(A_curr, axis=1, keepdims=True)
    for k in range(K):
        indx = np.where(y == k)
        plt.plot(X_init[indx, 0], X_init[indx, 1], color=COLOURS[k], marker=MARKERS[k], alpha=0.1)
        plt.plot(X_curr[indx, 0], X_curr[indx, 1], color=COLOURS[k], marker=MARKERS[k])

        plt.plot((0.0, A_curr[k, 0]), (0.0, A_curr[k, 1]), color=COLOURS[k])

    plt.gca().set_xlim(-3, 3)
    plt.gca().set_ylim(-3, 3)
    plt.title('Feature Space')

    plt.subplot(1, 2, 2)
    plt.gca().clear()
    plt.semilogy(loss_curve, 'k')
    plt.gca().set_xlim(0, len(loss_curve))
    plt.gca().set_ylim(1.0e-5, 1.0e1)
    plt.title('Learning Curve')
    plt.grid(True)

    return fig

import torch

# initial data
X_init = np.random.randn(N, D)
y = np.random.randint(low=0, high=K, size=N)

# unconstrained feature model
target = torch.tensor(y, dtype=torch.long)
X = torch.tensor(X_init, dtype=torch.float).clone().detach().requires_grad_(True)
classifier = torch.nn.Linear(D, K, bias=True)
theta = [torch.nn.Parameter(X), *classifier.parameters()]
optimizer = torch.optim.AdamW(theta, lr=0.05)

# animate optimization
fig, video = None, None
max_iters = 1000
loss_curve = [None for i in range(max_iters)]
for i in range(max_iters):
    print("\r...{} of {}".format(i + 1, max_iters), end='')

    # do optimization step
    optimizer.zero_grad()
    loss = torch.nn.functional.cross_entropy(classifier(theta[0]), target)
    loss_curve[i] = loss.item()
    loss.backward()
    optimizer.step()

    # visualize optimization state
    if VID_FILENAME:
        fig = visualize_state(X_init, X.detach().numpy(), theta[1].detach().numpy(), loss_curve, fig)
        fig.canvas.draw()
        img = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8)
        img = img.reshape(fig.canvas.get_width_height()[::-1] + (4,))

        # write video frame
        if video is None:
            width, height, _ = img.shape
            fourcc = cv2.VideoWriter_fourcc(*'h264')
            video = cv2.VideoWriter(VID_FILENAME, fourcc, 30, (height, width))

        video.write(img[:, :, 1:4])

if video:
    video.release()

# show last frame
visualize_state(X_init, X.detach().numpy(), theta[1].detach().numpy(), loss_curve, fig)
plt.show()

