#modified from pytorch github/example/reinforcement_learning
import argparse
import numpy as np
from itertools import count

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.distributions import Categorical

import subprocess
from subprocess import Popen, PIPE, call
import time
import sys
import os
import random
from datetime import datetime
import pickle

timenow = datetime.now()
torch.manual_seed(timenow.second)
random.seed(timenow.second)

class Policy(nn.Module):
    def __init__(self):
        super(Policy, self).__init__()
        self.affine1 = nn.Linear(2, 128)
        self.dropout = nn.Dropout(p=0.6)
        self.affine2 = nn.Linear(128, 2)

        self.saved_log_probs = []
        self.rewards = []

    def forward(self, x):
        x = self.affine1(x)
        x = self.dropout(x)
        x = F.relu(x)
        action_scores = self.affine2(x)
        return F.softmax(action_scores, dim=1)

policy = Policy()
optimizer = optim.Adam(policy.parameters(), lr=1e-2)
eps = np.finfo(np.float32).eps.item()
datadict = {}

def select_action(state):
    state = torch.from_numpy(state).float().unsqueeze(0)
    probs = policy(state)
    m = Categorical(probs)
    action = m.sample()
    policy.saved_log_probs.append(m.log_prob(action))
    return action.item()

def finish_episode(total_reward):
    total_log_probs = -torch.cat(policy.saved_log_probs).sum()
    optimizer.zero_grad()
    policy_loss = total_log_probs * total_reward
    policy_loss.backward()
    optimizer.step()
    del policy.saved_log_probs[:]
        
def runPingPong(msg_size, rx_delay):

def main():
    total_msg_sz = 0
    total_time = 0
    threshold = 100000
    while total_msg_sz < threshold:
        msg_size = random.randint(64, 20000)
        if msg_size + total_msg_sz > threshold:
            msg_size = threshold - total_msg_sz
        total_msg_sz += msg_size
        
        state = [msg_size]
        action = select_action(np.array(state))
        smsg_size = str(state[0])
        rx_delay = str(int(action) * 2)

        time_taken = runPingPong(smsg_size, rx_delay)
        print('msg_size=%s rx_delay=%s time_taken=%.6f' % (smsg_size, rx_delay, time_taken))
        datadict[smsg_size+","+rx_delay] = time_taken
        total_time += float(time_taken)

    reward = ((((total_msg_sz * 8) * 2) * 5000) / 1000000.0) / total_time
    print("reward = %.4f mbps" % (reward))
    finish_episode(reward)
    print("\t Saving model")
    torch.save(policy.state_dict(), "./reinforce_single_reward.pt")
    pickle.dump(datadict, open("reinforce_single_reward.dict", "wb"))
    
if __name__ == '__main__':
    try:
        print("Loading reinforce_single_reward.pt")
        policy.load_state_dict(torch.load("reinforce_test.pt"))
    except FileNotFoundError:
        print("reinforce_single_reward.pt not found")

    try:
        print("Loading reinforce_single_reward.dict")
        datadict = pickle.load(open("reinforce_test.dict", "rb"))
    except FileNotFoundError:
        print("reinforce_single_reward.dict not found")

    #main()
    #policy.eval()
    #for i in range(1, 250000):
    #    state = [i]
    #    action = select_action(np.array(state))
    #    msg_size = str(state[0])
    #    rx_delay = str(int(action))
    #    print(msg_size, rx_delay)

