import gym
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

plt.ion()
#device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
device = "cpu"

def runPingPong2(msg_size, rx_delay): 
    #if msg_size % 2 == 0: 
    '''
    #Option 1: doesn't work
    msg_size, rx_delay = float(msg_size), float(rx_delay)

    if msg_size > 10000:
        if 1.5 < rx_delay < 2.5: 
            val = 1
        else: 
            val = 0
    else: 
        if 7.5 < rx_delay < 8.5: 
            val = 1
        else: 
            val = 0

    return val
    '''

    #Option 2: continuous reward structure. works
    #return -torch.abs(msg_size - rx_delay)

    '''
    #Option 3: same as option 1 but recaled msg values. doesn't work.
    if msg_size > 4.5:
        if 1.5 < rx_delay < 2.5: 
            val = 1
        else: 
            val = 0
    else: 
        if 7.5 < rx_delay < 8.5: 
            val = 1
        else: 
            val = 0
    
    return val
    '''

    #option 4: continuous version of binary threshold. works
    optimal_delay = 9. / (1 + np.exp(-(msg_size - 4.5)/0.1))

    return -torch.abs(rx_delay - optimal_delay)




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
EPS_DECAY = 200
TARGET_UPDATE = 10
TIME_LENGTH = 10
STATE_STEP_SIZE = 0.1

num_episodes = 200
low_msg_size = 0
high_msg_size = 9

n_inputs = 1
n_actions = 10 #10-100 in steps of 100

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
    non_final_next_states = torch.cat([torch.tensor([s], device='cpu') for s in batch.next_state if s is not None]).unsqueeze(1)
    #state_batch = torch.cat(batch.state)
    #action_batch = torch.cat(batch.action)
    #reward_batch = torch.cat(batch.reward)

    state_batch = torch.cat([torch.tensor([s], device='cpu') for s in batch.state]).reshape(len(batch.state), 1)
    action_batch = torch.cat([torch.tensor([s], device='cpu') for s in batch.action]).reshape(len(batch.action), 1)
    reward_batch = torch.cat([torch.tensor([s], device='cpu') for s in batch.reward]).float()

    # Compute Q(s_t, a) - the model computes Q(s_t), then we select the
    # columns of actions taken. These are the actions which would've been taken
    # for each batch state according to policy_net
    state_action_values = policy_net(state_batch).gather(1, action_batch)

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

for i_episode in range(num_episodes):
    # Initialize the environment and state
    #env.reset()
    #last_screen = get_screen()
    #current_screen = get_screen()
    #state = current_screen - last_screen
    state = np.random.uniform(low_msg_size, high_msg_size)
    done = False

    for t in count():
        # Select and perform an action
        action = select_action(state)
        #_, reward, done, _ = env.step(action.item())
        reward = runPingPong2(state, action)
        reward = torch.tensor([reward], device=device)

        if t==TIME_LENGTH:
            done = True

        # Observe new state
        if not done:
            next_state = np.random.uniform(low_msg_size, high_msg_size)
            #next_state = state + (np.random.randint(2)-1) * STATE_STEP_SIZE
            #if next_state >= high_msg_size:
            #    next_state -= 2*STATE_STEP_SIZE
            #if next_state <= low_msg_size:
            #    next_state += 2*STATE_STEP_SIZE

        else:
            next_state = None

        # Store the transition in memory
        memory.push(state, action, next_state, reward)

        # Move to the next state
        state = next_state

        # Perform one step of the optimization (on the target network)
        #import pdb
        #pdb.set_trace()
        optimize_model()
        if done:
            episode_durations.append(t + 1)
            break
    print("Episode = ", i_episode)
    # Update the target network, copying all weights and biases in DQN
    if i_episode % TARGET_UPDATE == 0:
        target_net.load_state_dict(policy_net.state_dict())

print('Complete')
