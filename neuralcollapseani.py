# ANIMATION TO ILLUSTRATE NEURAL COLLAPSE
# Stephen Gould <stephen.gould@anu.edu.au>
#

import numpy as np
import matplotlib.pyplot as plt
import cv2

plt.rcParams.update({'font.size': 16})

N, K, D = 100, 3, 2
COLOURS = ('b', 'r', 'g', 'm')
MARKERS = ('o', '^', 'd', 's')
LINE_STYLES = ('k--', 'k-.')

VID_FILENAME = r"neural_collapse_{}.mp4"
#VID_FILENAME = None


def visualize_state(X_init, y, X_curr, A_curr, loss_curve, fig=None):
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


def animate_training(filename=None, fig=None, rnd_seed=22, max_iters=1000, A_init=None, ref_losses=[]):
    """Complete a training run. Generate video if `filename` is provided."""

    # initialize data
    np.random.seed(rnd_seed)
    torch.random.manual_seed(rnd_seed)
    X_init = np.random.randn(N, D)
    y = np.random.randint(low=0, high=K, size=N)

    # unconstrained feature model
    target = torch.tensor(y, dtype=torch.long)
    X = torch.tensor(X_init, dtype=torch.float).clone().detach().requires_grad_(True)
    classifier = torch.nn.Linear(D, K, bias=True)
    if A_init is None:
        theta = [torch.nn.Parameter(X), *classifier.parameters()]
    else:
        theta = [torch.nn.Parameter(X)]
        with torch.no_grad():
            classifier.weight.copy_(torch.tensor(A_init))
            classifier.bias.copy_(torch.zeros_like(classifier.bias))

    optimizer = torch.optim.AdamW(theta, lr=0.05)

    # animate optimization
    video = None
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
        if filename:
            fig = visualize_state(X_init, y, X.detach().numpy(), theta[1].detach().numpy() if A_init is None else A_init, loss_curve, fig)
            for i in range(len(ref_losses)):
                plt.semilogy(ref_losses[i], LINE_STYLES[i])
            fig.canvas.draw()
            img = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8)
            img = img.reshape(fig.canvas.get_width_height()[::-1] + (4,))

            # write video frame
            if video is None:
                width, height, _ = img.shape
                fourcc = cv2.VideoWriter_fourcc(*'h264')
                video = cv2.VideoWriter(filename, fourcc, 30, (height, width))

            video.write(img[:, :, 1:4])

    if video:
        video.release()

    # show last frame
    fig = visualize_state(X_init, y, X.detach().numpy(), theta[1].detach().numpy() if A_init is None else A_init, loss_curve, fig)
    for i in range(len(ref_losses)):
        plt.semilogy(ref_losses[i], LINE_STYLES[i])
    return fig, loss_curve


# training run with free classifier
filename = VID_FILENAME.format("free") if VID_FILENAME else None
fig, loss_free = animate_training(filename)

# training with fixed classifier
filename = VID_FILENAME.format("fixed") if VID_FILENAME else None
A_init = 2.0 * np.array([[-0.71, 0.71], [-0.71, -0.71], [1.0, 0.0]])
fig, loss_fixed = animate_training(filename, fig=None, A_init = A_init, ref_losses=[loss_free])
plt.legend(['fixed', 'free'])

# pause to show figures
plt.show()

