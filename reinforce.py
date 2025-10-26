# REINFORCE ALGORITHM ON GRID
# Stephen Gould <stephen.gould@anu.edu.au>
#

import numpy as np
import matplotlib.pyplot as plt

import torch
import torch.nn as nn

import tqdm


class GridWorld:
    def __init__(self, n, m, init_pos, goal_pos):
        assert len(init_pos) == len(goal_pos) == 2
        assert (0 <= init_pos[0] < m) and (0 <= init_pos[1] < n)
        assert (0 <= goal_pos[0] < m) and (0 <= goal_pos[1] < n)

        self.n, self.m = n, m
        self.position = init_pos
        self.goal = goal_pos

    def move(self, direction):
        x, y = self.position
        if direction == 0:      # north
            self.position = (x, max(y - 1, 0))
        elif direction == 1:    # south
            self.position = (x, min(y + 1, self.n - 1))
        elif direction == 2:    # east
            self.position = (min(x + 1, self.m - 1), y)
        elif direction == 3:    # west
            self.position = (max(x - 1, 0), y)

    def at_goal(self):
        return self.position == self.goal

    def get_state(self, device):
        return torch.FloatTensor(np.concatenate((self.position, self.goal))).unsqueeze(0).to(device)

    def __str__(self):
        return "\n".join(["".join(["P" if self.position == (i, j) else "G" if self.goal == (i, j) else "." for i in range(self.m)]) for j in range(self.n)])


def sample_world(n=5, m=5):
    goal_pos = (np.random.randint(m), np.random.randint(n))
    #goal_pos = (0, 0)
    init_pos = (np.random.randint(m), np.random.randint(n))
    #init_pos = (m-1, n-1)
    while goal_pos == init_pos:
        init_pos = (np.random.randint(m), np.random.randint(n))

    return GridWorld(n, m, init_pos, goal_pos)


class PolicyModel(nn.Module):
    def __init__(self):
        super(PolicyModel, self).__init__()
        self.fc1 = nn.Linear(4, 16)
        self.fc2 = nn.Linear(16, 4)

    def forward(self, x):
        z = nn.functional.relu(self.fc1(x))
        y = nn.functional.softmax(self.fc2(z), dim=1)
        return y


def generate_episode(world, policy, device="cpu", max_episode_len=100):
    state = world.get_state(device)
    ep_length = 0
    while not world.at_goal():
        ep_length += 1
        p_action = policy(state).squeeze()
        log_p_action = torch.log(p_action)
        action = np.random.choice(np.arange(4), p=p_action.detach().cpu().numpy())

        world.move(action)
        next_state = world.get_state(device)
        reward = -0.1 if not world.at_goal() else 0.0

        sample = (state, action, reward)
        yield sample, log_p_action

        if reward == 0.0:
            break

        state = next_state
        if ep_length > max_episode_len:
            return

    sample = (world.get_state(device), None, 0.0)
    yield sample, log_p_action


def gradients_wrt_params(net, loss):
    for name, param in net.named_parameters():
        g = torch.autograd.grad(loss, param, retain_graph=True)[0]
        param.grad = g

def update_params(net, lr):
    for name, param in net.named_parameters():
        param.data += lr * param.grad


# --- tests ---

if False:
    world = sample_world()
    print(world, "\n")
    world.move(1)
    print(world, "\n")
    world.move(0)
    print(world, "\n")

    exit(0)

# --- learning ---

device = "cpu"
policy = PolicyModel()
policy.to(device)

lengths = []
rewards = []

gamma = 0.99
learning_rate = 1.0e-3

optimizer = torch.optim.AdamW(policy.parameters(), lr=learning_rate)
for episode_num in tqdm.tqdm(range(5000)):
    all_iterations = []
    all_log_probs = []
    world = sample_world()
    episode = list(generate_episode(world, policy, device=device))
    lengths.append(len(episode))
    loss = 0
    for t, ((state, action, reward), log_probs) in enumerate(episode[:-1]):
        gammas_vec = gamma ** (torch.arange(t+1, len(episode))-t-1)
        G = -0.1 * torch.sum(gammas_vec)
        rewards.append(G.item())
        policy_loss = log_probs[action]
        optimizer.zero_grad()
        gradients_wrt_params(policy, policy_loss)
        update_params(policy, learning_rate  * G * gamma**t)


plt.figure()
plt.plot(lengths)

plt.figure()
plt.plot(rewards)

plt.show()