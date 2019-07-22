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

SERVER = "192.168.1.200"
            
class Policy(nn.Module):
    def __init__(self):
        super(Policy, self).__init__()
        self.affine1 = nn.Linear(1, 128)
        self.dropout = nn.Dropout(p=0.6)
        self.affine2 = nn.Linear(128, 40)

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
    
def runLocalCommand(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)

def runRemoteCommand(com):
    p1 = Popen(["ssh", SERVER, com], stdout=PIPE, stderr=PIPE)
    
def runRemoteCommandOut(com):
    p1 = Popen(["ssh", SERVER, com], stdout=PIPE)
    print("\tssh "+SERVER, com, "->\n", p1.communicate()[0].strip())
    
def runLocalCommandOut(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    print("\t"+com, "->\n", p1.communicate()[0].strip())

def runNetPipe(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE, stderr=PIPE)
    time.sleep(1)
    stdout, stderr = p1.communicate()
    if len(stderr) == 0:
        return 0.0
    else:
        lines=list(filter(None, str(stderr).strip().split('-->')))
        lines2=list(filter(None, lines[1].strip().split(' ')))
        return float(lines2[5])
    
def runPingPong(msg_size, rx_delay):
    runRemoteCommand("pkill NPtcp")
    time.sleep(0.1)
    runLocalCommand("pkill NPtcp")
    time.sleep(0.1)
    runRemoteCommand("ethtool -C enp4s0f1 rx-usecs "+rx_delay)
    time.sleep(0.5)
    runRemoteCommand("taskset -c 1 NPtcp -l "+msg_size+" -u "+msg_size+"-p 0 -r -I")
    time.sleep(1)
    return runNetPipe("taskset -c 1 NPtcp -h "+SERVER+" -l "+msg_size+" -u "+msg_size+" -n 5000 -p 0 -r -I")

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
        policy.load_state_dict(torch.load("reinforce_single_reward.pt"))
    except FileNotFoundError:
        print("reinforce_single_reward.pt not found")

    try:
        print("Loading reinforce_single_reward.dict")
        datadict = pickle.load(open("reinforce_single_reward.dict", "rb"))
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

