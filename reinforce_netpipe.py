#modified from pytorch github/example/reinforcement_learning
import argparse
import gym
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

#parser = argparse.ArgumentParser(description='PyTorch REINFORCE netpipe example')
#parser.add_argument('--gamma', type=float, default=0.99, metavar='G',
#                    help='discount factor (default: 0.99)')
#parser.add_argument('--render', action='store_true',
#                    help='render the environment')
#parser.add_argument('--log-interval', type=int, default=10, metavar='N',
#                    help='interval between training status logs (default: 10)')
#parser.add_argument('--ttype', type=int, default=0, metavar='N',
#                    help='type')

gamma = 0.99
#args = parser.parse_args()
timenow = datetime.now()
torch.manual_seed(timenow.second)
random.seed(timenow.second)

linux_default = pickle.load(open("linux_default.pickle", "rb"))
SERVER = "192.168.1.200"
            
class Policy(nn.Module):
    def __init__(self):
        super(Policy, self).__init__()
        # 1 message size IN, 100 interrupt delays out
        self.affine1 = nn.Linear(1, 128)
        self.dropout = nn.Dropout(p=0.6)
        self.affine2 = nn.Linear(128, 80)

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

def select_action(state):
    state = torch.from_numpy(state).float().unsqueeze(0)
    probs = policy(state)
    m = Categorical(probs)
    action = m.sample()
    policy.saved_log_probs.append(m.log_prob(action))
    return action.item()

def finish_episode():
    R = 0
    policy_loss = []
    returns = []
    for r in policy.rewards[::-1]:
        R = r + gamma * R
        returns.insert(0, R)
    returns = torch.tensor(returns)
    returns = (returns - returns.mean()) / (returns.std() + eps)
    for log_prob, R in zip(policy.saved_log_probs, returns):
        policy_loss.append(-log_prob * R)
    optimizer.zero_grad()
    policy_loss = torch.cat(policy_loss).sum()
    policy_loss.backward()
    #print("policy_loss", policy_loss)
    optimizer.step()
    del policy.rewards[:]
    del policy.saved_log_probs[:]

def finish_episode2(total_reward):
    total_log_probs = -torch.cat(policy.saved_log_probs).sum()
    #total_log_probs = torch.cat(policy.saved_log_probs).sum()
    #print("total_log_probs", total_log_probs)
    optimizer.zero_grad()
    policy_loss = total_log_probs * total_reward
    policy_loss.backward()
    #print("policy_loss", policy_loss)
    optimizer.step()
    del policy.saved_log_probs[:]
    
def runLocalCommand(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)

def runRemoteCommand(com):
    p1 = Popen(["ssh", SERVER, com], stdout=PIPE)
    
def runRemoteCommandOut(com):
    p1 = Popen(["ssh", SERVER, com], stdout=PIPE)
    print("\tssh "+SERVER, com, "->\n", p1.communicate()[0].strip())
    
def runLocalCommandOut(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    print("\t"+com, "->\n", p1.communicate()[0].strip())

def runNetPipe(com, t):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE, stderr=PIPE)
    time.sleep(1)
    stdout, stderr = p1.communicate()
    if len(stderr) == 0:
        return 0.0
    else:
        lines=list(filter(None, str(stderr).strip().split('-->')))
        lines2=list(filter(None, lines[1].strip().split(' ')))
        print(lines2)
        if t == 1:
            return float(lines2[0])
        else:
            return float(lines2[5])
    
def runPingPong(msg_size, rx_delay, t):
    runRemoteCommand("pkill NPtcp")
    time.sleep(1)
    runLocalCommand("pkill NPtcp")
    time.sleep(1)
    runRemoteCommand("ethtool -C enp4s0f1 rx-usecs "+rx_delay)
    time.sleep(1)
    runRemoteCommand("taskset -c 1 NPtcp -l "+msg_size+" -u "+msg_size+"-p 0 -r -I")
    time.sleep(2)
    return runNetPipe("taskset -c 1 NPtcp -h "+SERVER+" -l "+msg_size+" -u "+msg_size+" -n 1 -p 0 -r -I", t)

def mainLinuxCompare(tt):
    running_reward = 5
    for i_episode in range(1, 2):
        print("************** Episode", i_episode, "**************")
        ep_reward = 0
        for t in range(1, 100):
            state = []
            state.append(random.randint(64, 20000))
            print('\t step='+str(t)+' state='+str(state[0]), end=' ', flush=True)
            action = select_action(np.array(state))
            print('action='+str(int(action)), end=' ', flush=True)
                        
            msg_size = str(state[0])
            rx_delay = str(int(action))
            tput = runPingPong(msg_size, rx_delay, tt)
            print('tput='+str(tput), end=' ', flush=True)
                        
            if msg_size not in linux_default:
                linux_default[msg_size] = tput
                reward = 0.0
                print("\t msg_size=",msg_size,"not in linux_default")
            else:
                linux_tput = linux_default[msg_size]
                reward = tput - linux_tput
            
            policy.rewards.append(reward)
            ep_reward += reward
            print("reward="+str(reward))
            
        running_reward = 0.05 * ep_reward + (1 - 0.05) * running_reward
        finish_episode()
        print("\t Saving model to reinforce2.pt")
        torch.save(policy.state_dict(), "./reinforce2.pt")
        print('************** Episode {}\tLast reward: {:.2f}\tAverage reward: {:.2f} **************'.format(i_episode, ep_reward, running_reward))
        print("")

def main(t):
    total_msg_sz = 0
    total_time = 0
    threshold = 1000000
    while total_msg_sz < threshold:
        msg_size = random.randint(1, 20000)
        if msg_size + total_msg_sz > threshold:
            msg_size = threshold - total_msg_sz
        total_msg_sz += msg_size
        
        state = []
        state.append(msg_size)
        action = select_action(np.array(state))
        smsg_size = str(state[0])
        rx_delay = str(int(action))
        time_taken = runPingPong(smsg_size, rx_delay, t)
        total_time += float(time_taken)
        print('msg_size=%s rx_delay=%s time_taken=%.6f' % (smsg_size, rx_delay, time_taken))

    reward = ((threshold*8)/1000000.0)/total_time
    print("reward = %.2f mbps" % (reward))
    finish_episode2(reward)
    print("\t Saving model to reinforce_one_reward2.pt")
    torch.save(policy.state_dict(), "./reinforce_one_reward2.pt")
    
if __name__ == '__main__':
    #policy.load_state_dict(torch.load("./reinforce2.pt"))
    #policy.eval()
    #for i in range(1, 200000):
    #    state = []
    #    state.append(i)
    #    action = select_action(np.array(state))
    #    msg_size = str(state[0])
    #    rx_delay = str(int(action))
    #    print("%s,%s" % (msg_size, rx_delay))

    if int(sys.argv[1]) == 1:
        #print("Loading model reinforce2.pt")
        #policy.load_state_dict(torch.load("./reinforce2.pt"))
        mainLinuxCompare(1)
    else:
        print("Loading model reinforce_one_reward2.pt")
        policy.load_state_dict(torch.load("./reinforce_one_reward2.pt"))
        main(2)
        
#    for i in range(0, 81, 2):
#        print(i, end=' ', flush=True)
 

#    policy.load_state_dict(torch.load("./reinforce_one_reward.pt"))
    #policy.eval()
#    for i in range(1, 200000):
#        state = []
#        state.append(i)
#        action = select_action(np.array(state))
#        msg_size = str(state[0])
#        rx_delay = str(int(action))
#        print("%s,%s" % (msg_size, rx_delay))
        #print(rx_delay,"us ", msg_size, "bytes ")
        
#    mainLinuxCompare()
    #main()
#    print("Saving model to reinforce.pt")
#    torch.save(policy.state_dict(), "./reinforce.pt")
            
'''    
    for i in range(1, 250000):
        state = []
        state.append(i)
        action = select_action(np.array(state))
        msg_size = str(state[0])
        rx_delay = str(int(action))
        #if rx_delay != "8":
        print("\t",rx_delay,"us ", msg_size, "bytes ")


'''
