import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

import math
import random
import numpy as np

device = "cpu"

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

n_inputs = 1   # msg size
n_actions = 100 # rx_delay == [0, 2, ..., 200]
target_net = DQN(n_inputs, n_actions).to("cpu")
low_msg_size = 512
high_msg_size = 32768

try:
    print("Loading qlearn_netpipe87.pt")
    target_net.load_state_dict(torch.load("qlearn_netpipe87.pt"))
except FileNotFoundError:
    print("qlearn_netpipe87.pt not found")

print("Training Complete")
print("target_net eval now:")
target_net.eval()
mdict = {}
list27 = []
list45 = []
list17 = []
for i in range(low_msg_size, high_msg_size):
    state = torch.from_numpy(np.array([i])).float().unsqueeze(0).to(device)
    with torch.no_grad():
        key = int(target_net(state).max(1)[1].view(1, 1).item())
        if key == 27:
            list27.append(i)
        elif key == 17:
            list17.append(i)
        elif key == 45:
            list45.append(i)

print("34: ", len(list17), min(list17), max(list17))
print("54: ", len(list27), min(list27), max(list27))
print("90: ", len(list45), min(list45), max(list45))

