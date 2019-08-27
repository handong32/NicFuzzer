import math
import random
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from collections import namedtuple
from itertools import count

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

import subprocess
from subprocess import Popen, PIPE, call
import time
from datetime import datetime
import sys
import os
import getopt
import pickle

device = "cpu"

LSERVER = "192.168.1.201"
CSERVER = "192.168.1.200"
#linuxdef = {}
static_tput_watt = {}

torch.manual_seed(0)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
np.random.seed(0)

def runLocalCommandOut(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    print("\t"+com, "->\n", p1.communicate()[0].strip())
    
def runRemoteCommandOut(server, com):
    p1 = Popen(["ssh", server, com], stdout=PIPE)
    print("\tssh "+server, com, "->\n", p1.communicate()[0].strip())

def runRemoteCommandGet(server, com):
    p1 = Popen(["ssh", server, com], stdout=PIPE)
    return p1.communicate()[0].strip()
    
def runLocalCommand(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    
def runRemoteCommand(server, com):
    p1 = Popen(["ssh", server, com], stdout=PIPE)
    
Transition = namedtuple('Transition',
                        ('state', 'action', 'next_state', 'reward'))

class ReplayMemory(object):
    def __init__(self, capacity):
        self.capacity = capacity
        self.memory = []
        self.position = 0

    def push(self, *args):
        if len(self.memory) < self.capacity:
            self.memory.append(None)
        self.memory[self.position] = Transition(*args)
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)

class DQN(nn.Module):
    def __init__(self, inputs, outputs):
        super(DQN, self).__init__()
        
        self.affine1 = nn.Linear(inputs, 32) #state-action
        self.affine2 = nn.Linear(32, 32)
        self.head = nn.Linear(32, outputs) #output: q-value

    def forward(self, x):
        #x = F.relu(self.bn1(self.conv1(x)))
        #x = F.relu(self.bn2(self.conv2(x)))
        #x = F.relu(self.bn3(self.conv3(x)))
        #return self.head(x.view(x.size(0), -1))        

        x = F.relu(self.affine1(x))
        x = F.relu(self.affine2(x))
        x = self.head(x)

        return x

BATCH_SIZE = 128
GAMMA = 0.999
EPS_START = 0.9
EPS_END = 0.05
EPS_DECAY = 2000
TARGET_UPDATE = 10
TIME_LENGTH = 10
STATE_STEP_SIZE = 0.1

num_episodes = 961
low_msg_size = 512
high_msg_size = 131072
    
n_inputs = 1   # msg size
n_actions = 50 # rx_delay == [0, 2, ..., 100]

policy_net = DQN(n_inputs, n_actions).to(device)
target_net = DQN(n_inputs, n_actions).to(device)
target_net.load_state_dict(policy_net.state_dict())
target_net.eval()

optimizer = optim.RMSprop(policy_net.parameters())
memory = ReplayMemory(10000)

steps_done = 0

def select_action(state):
    global steps_done
    
    steps_done += 1
    sample = np.random.random()
    eps_threshold = EPS_END + (EPS_START - EPS_END) * \
                    math.exp(-1. * steps_done / EPS_DECAY)
    state = torch.from_numpy(np.array([state])).float().unsqueeze(0).to(device)
    
    if sample < eps_threshold:
        return torch.tensor([[random.randrange(n_actions)]], device=device, dtype=torch.long)
    else:
        with torch.no_grad():
            return policy_net(state).max(1)[1].view(1, 1)

episode_durations = []

def optimize_model():
    if len(memory) < BATCH_SIZE:
        return

    transitions = memory.sample(BATCH_SIZE)
    # Transpose the batch (see https://stackoverflow.com/a/19343/3343043 for
    # detailed explanation). This converts batch-array of Transitions
    # to Transition of batch-arrays.
    batch = Transition(*zip(*transitions))

    # Compute a mask of non-final states and concatenate the batch elements
    # (a final state would've been the one after which simulation ended)
    non_final_mask = torch.tensor(tuple(map(lambda s: s is not None, batch.next_state)), device=device, dtype=torch.uint8)
    #non_final_next_states = torch.cat([s for s in batch.next_state if s is not None])
    non_final_next_states = torch.cat([torch.tensor([s], device=device) for s in batch.next_state if s is not None]).unsqueeze(1)
    #state_batch = torch.cat(batch.state)
    #action_batch = torch.cat(batch.action)
    #reward_batch = torch.cat(batch.reward)

    state_batch = torch.cat([torch.tensor([s], device=device) for s in batch.state]).reshape(len(batch.state), 1)
    action_batch = torch.cat([torch.tensor([s], device=device) for s in batch.action]).reshape(len(batch.action), 1)
    reward_batch = torch.cat([torch.tensor([s], device=device) for s in batch.reward]).float()

    # Compute Q(s_t, a) - the model computes Q(s_t), then we select the
    # columns of actions taken. These are the actions which would've been taken
    # for each batch state according to policy_net
    try:
        state_action_values = policy_net(state_batch).gather(1, action_batch)
    except:
        print("*********** gather ERROR")
        import pdb
        pdb.set_trace()
        
    # Compute V(s_{t+1}) for all next states.
    # Expected values of actions for non_final_next_states are computed based
    # on the "older" target_net; selecting their best reward with max(1)[0].
    # This is merged based on the mask, such that we'll have either the expected
    # state value or 0 in case the state was final.
    next_state_values = torch.zeros(BATCH_SIZE, device=device)
    next_state_values[non_final_mask] = target_net(non_final_next_states).max(1)[0].detach()
    # Compute the expected Q values
    expected_state_action_values = (next_state_values * GAMMA) + reward_batch

    # Compute Huber loss
    loss = F.smooth_l1_loss(state_action_values, expected_state_action_values.unsqueeze(1))

    # Optimize the model
    optimizer.zero_grad()
    loss.backward()
    for param in policy_net.parameters():
        param.grad.data.clamp_(-1, 1)
    optimizer.step()        

def runBench(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE, stderr=PIPE)
    time.sleep(1)
    stdout, stderr = p1.communicate()
    if len(stderr) == 0:
        printf("*** len(stderr) == 0")
        return 0
    else:
        print(stderr)
        try:
            lines=list(filter(None, str(stderr).strip().split('-->')))
            lines2=list(filter(None, lines[1].strip().split(' ')))
            return float(lines2[0])
        except IndexError:
            print("******* IndexError:", str(stderr))
            return 0

def runLinux(msg_size):
    runRemoteCommand(LSERVER, "pkill NPtcp")
    time.sleep(0.1)
    runLocalCommand("pkill NPtcp")
    time.sleep(0.1)
    runRemoteCommand(LSERVER, "taskset -c 1 NPtcp -l "+msg_size+" -u "+msg_size+"-p 0 -r -I")
    time.sleep(1)
    return runBench("taskset -c 1 NPtcp -h "+LSERVER+" -l "+msg_size+" -u "+msg_size+" -T 1 -p 0 -r -I")

def runStatic(msg_size, rx_delay):
    runRemoteCommand(CSERVER, "pkill NPtcp")
    time.sleep(0.5)
    runLocalCommand("pkill NPtcp")
    time.sleep(0.5)
    runRemoteCommand(CSERVER, "ethtool -C enp4s0f1 rx-usecs "+rx_delay)
    time.sleep(0.5)
    runRemoteCommand(CSERVER, "perf stat -C 1 -D 1000 -o perf.out -e power/energy-pkg/,power/energy-ram/ -x, taskset -c 1 NPtcp -l "+msg_size+" -u "+msg_size+"-p 0 -r -I")
    time.sleep(1)
    start = datetime.now()
    tput = runBench("taskset -c 1 NPtcp -h "+CSERVER+" -l "+msg_size+" -u "+msg_size+" -T 5 -p 0 -r -I")
    end = datetime.now()
    secs = (end - start).total_seconds()
    return tput, secs

def getPower(s):
    p = runRemoteCommandGet(CSERVER, "cat perf.out")
    time.sleep(0.5)
    sum_joules = 0.0
    for l in str(p).split('\\n'):
        if 'Joules' in l:
            sum_joules += float(l.split(',')[0])
    if s > 0:
        return sum_joules/s
    else:
        return 0
    
def runNetPipe():
    for i_episode in range(num_episodes):
        state = float(np.random.randint(low_msg_size, high_msg_size))
        done = False

        mcnt = 0
        for t in count():
            # Select and perform an action
            action = select_action(state)

            ltput = -1
            laction = -1
            ltputwatts = 0
            ctputwatts = 0
            lsecs = 0
            csecs = 0
            
            if state not in static_tput_watt.keys():
                laction = np.random.randint(n_inputs, n_actions) * 2
                ltput,lsecs = runStatic(str(state), str(laction))
                lpower = float(getPower(lsecs))
                if lpower > 0:
                    ltputwatts = ltput/lpower
                else:
                    ltputwatts = 0
            else:
                ltputwatts = static_tput_watt[state]
                
            ctput, csecs = runStatic(str(state), str(action.item() * 2))
            cpower = float(getPower(csecs))
            if cpower > 0:
                ctputwatts = ctput/cpower
            else:
                ctputwatts = 0
                
            if ctputwatts > 0 and ltputwatts > 0:
                mcnt += 1
                # keep history of highest throughput seen thus far for some msg size (state)
                if ltputwatts > ctputwatts:
                    static_tput_watt[state] = ltputwatts
                else:
                    static_tput_watt[state] = ctputwatts
                
                reward = torch.tensor((ctputwatts-ltputwatts)/ltputwatts) # % improvement over linux default
                reward = torch.tensor([reward], device=device)
                print("EP=%d t=%d MSG=%d Laction=%d Ltput=%.6f LtputWatts=%.6f Caction=%d Ctput=%.6f CtputWatts=%.6f REWARD=%.6f" % (i_episode, t, state, laction, ltput, ltputwatts, action.item()*2, ctput, ctputwatts, reward))
                
                if mcnt==TIME_LENGTH:
                    done = True

                # Observe new state
                if not done:
                    next_state = float(np.random.randint(low_msg_size, high_msg_size))
                else:
                    next_state = None

                # Store the transition in memory
                memory.push(state, action, next_state, reward)

                # Move to the next state
                state = next_state

                # Perform one step of the optimization (on the target network)
                optimize_model()
                if done:
                    episode_durations.append(t + 1)
                    break

        # Update the target network, copying all weights and biases in DQN
        if i_episode % TARGET_UPDATE == 0:
            print("\t Saving target_net")
            target_net.load_state_dict(policy_net.state_dict())
            torch.save(target_net.state_dict(), "target_net810.pt")
            torch.save(policy_net.state_dict(), "policy_net810.pt")
            
        # log linux history
        pickle.dump(static_tput_watt, open("static_tput_watt_8_9.pickle", "wb"))

def runNetpipe2(fn):
    f = open(fn, 'r')
    mdict = {}
    for l in f:
        tmp = l.split(" ")
        msg = 0
        action = 0
        tput = 0
        for t in tmp:
            if "MSG=" in t:
                msg = int(t.split("=")[1])
            if "Laction=" in t:
                action = int(t.split("=")[1]) / 2
            if "Ltput=" in t:
                tput = float(t.split("=")[1])

        if msg not in mdict.keys():
            mdict[msg] = [action, tput]
        else:
            if tput > mdict[msg][1]:
                mdict[msg] = [action, tput]
    f.close()
    #print(mdict)

    ldict = list(mdict.keys())
    print(ldict[0], ldict[len(ldict)-1])
    
    for i in range(0, len(ldict)):
        state = ldict[i]
        next_state = None
        if i + 1 < len(ldict):
            next_state = ldict[i+1]
            next_state = torch.from_numpy(np.array([next_state], dtype=np.int32)).float().unsqueeze(0).to(device)
            
        action = mdict[state][0]
        reward = torch.tensor([mdict[state][1]], device=device)
        action = torch.tensor([action], device=device, dtype=torch.long)
        state = torch.from_numpy(np.array([state])).float().unsqueeze(0).to(device)
        memory.push(state, action, next_state, reward)
        optimize_model()

    target_net.load_state_dict(policy_net.state_dict())

    print("Training Complete")
    print("target_net eval now:")
    target_net.eval()
    #adict = {}
    prev = 0
    for i in range(low_msg_size, high_msg_size):
        state = torch.from_numpy(np.array([i])).float().unsqueeze(0).to(device)
        with torch.no_grad():
            action = int(target_net(state).max(1)[1].view(1, 1).item())*2
            if action != prev:
                print("Msg=", i, " Action=", action)
                prev = action
            
            #if key not in adict.keys():
            #    adict[key] = 0
            #else:
            #    adict[key] += 1

    #print(adict)
    
runNetpipe2("tmp.log")

    
'''
def runNetpipe3(fn):
    f = open(fn, 'r')
    mdict = {}
    for l in f:
        tmp = l.split(" ")
        msg = 0
        action = 0
        tput = 0
        for t in tmp:
            if "MSG=" in t:
                msg = int(t.split("=")[1])
            if "Laction=" in t:
                action = int(t.split("=")[1]) / 2
            if "Ltput=" in t:
                tput = float(t.split("=")[1])

        if msg > 9600 and msg < 10600:
            print(l.strip())
        if msg not in mdict.keys():
            mdict[msg] = [action, tput]
        else:
            if tput > mdict[msg][1]:
                mdict[msg] = [action, tput]
    f.close()
    #print(mdict)

runNetpipe3("tmp.log")

if __name__ == '__main__':
    try:
        print("Loading static_tput_watt_8_9.pickle", end=" ")
        static_tput_watt = pickle.load(open("static_tput_watt_8_9.pickle", "rb"))
        print(len(static_tput_watt))
    except FileNotFoundError:
        print("static_tput_watt_8_9.pickle not found")

    #    runNetPipe()
    try:
        target_net.load_state_dict(torch.load("target_net810.pt"))
    except FileNotFoundError:
        print("qlearn_netpipe87.pt not found")

        
    print("Training Complete")
    print("target_net eval now:")
    target_net.eval()
    mdict = {}
    for i in range(low_msg_size, high_msg_size):
        state = torch.from_numpy(np.array([i])).float().unsqueeze(0).to(device)
        with torch.no_grad():
            key = int(target_net(state).max(1)[1].view(1, 1).item())*2
            #print(i, key)
            if key not in mdict.keys():
                mdict[key] = 0
            else:
                mdict[key] += 1

    print(mdict)
''' 
'''
try:
        print("Loading qlearn_netpipe87.pt")
target_net.load_state_dict(torch.load("qlearn_netpipe87.pt"))
    except FileNotFoundError:
        print("qlearn_netpipe87.pt not found")
        
    try:
        print("Loading linuxdef87.pickle", end=" ")
        linuxdef = pickle.load(open("linuxdef87.pickle", "rb"))
        print(len(linuxdef))
    except FileNotFoundError:
        print("linuxdef87.pickle not found")
'''
