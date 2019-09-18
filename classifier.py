import numpy as np
import pandas as pd

import torch
import torch.nn as nn
import torch.optim as optim

'''
def generate_data(N=1000):
    x1 = np.random.randint(0, 10000, size=N)
    y1 = 2 * np.ones(N)

    x2 = np.random.randint(10000, 20000, size=N)
    y2 = 7 * np.ones(N)

    x = np.concatenate([x1, x2])
    y = np.concatenate([y1, y2])

    return x,y
'''

def generate_data(L=10, stepsize=0.1):
    x = np.arange(-L, L, stepsize)
    #y = np.sin(3*x) * np.exp(-x / 8.)
    #y = np.sin(x)

    y = x.copy()
    y[y<0] = -1
    y[y>=0] = 1
    y = y + 5

    return x, y

class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.affine1 = nn.Linear(1, 32)
        self.affine2 = nn.Linear(32, 32)
        self.affine3 = nn.Linear(32, 50)
        self.logsoftmax = nn.LogSoftmax(dim=1)

    def forward(self, x):
        x = self.affine1(x)
        x = torch.sigmoid(x)

        x = self.affine2(x)
        x = torch.sigmoid(x)

        x = self.affine3(x)
        x = torch.sigmoid(x)

        x = self.logsoftmax(x)

        return x

def train(x, y, net, N_epochs):
    x = torch.tensor(x).reshape(len(x), 1).float()
    #y = torch.tensor(y).float().reshape(len(y), 1).float()
    y = torch.tensor(y).reshape(len(y), 1).long()

    optimizer = optim.Adam(net.parameters(), lr=1e-3)
    criterion = nn.NLLLoss()
    #criterion = nn.MSELoss()

    for epoch in range(N_epochs):
        pred = net(x)
        y = y.reshape(len(y))
        loss = criterion(pred, y)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        #if epoch % 100 == 0:
        #    print(f'Epoch = {epoch} Loss = {loss}')

    return net, x, y

#x, y = generate_data()
#print(x)
#print(y)

#net = Net()
#net, x, y = train(x, y, net, 500)
#net.eval()
#x = [-50.0, -40.0, 1.5, 0.235, -0.645]
#x = torch.tensor(x).reshape(len(x), 1).float()
#outputs = net(x)
#_, predicted = torch.max(outputs.data, 1)
#print(predicted)
#print(x)
#print(y)

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

    x = []
    y = []
    for k, v in mdict.items():
        x.append(int(k))
        y.append(int(v[0]))
        print(int(k), int(v[0])*2)
    return

    net = Net()
    net, x, y = train(x, y, net, 5000)
    net.eval()
    x = range(512, 120000)
    print(x)
    x = torch.tensor(x).reshape(len(x), 1).float()
    outputs = net(x)
    _, predicted = torch.max(outputs.data, 1)
    prev = 0
    for i in predicted:
        if i*2 != prev:
            print(i*2)
            prev = i*2
    #print(x)
    #print(y)
#    print("Training Complete")
#    print("target_net eval now:")
#    target_net.eval()
    #adict = {}
#    prev = 0
#    for i in range(low_msg_size, high_msg_size):
#        state = torch.from_numpy(np.array([i])).float().unsqueeze(0).to(device)
#        with torch.no_grad():
#            action = int(target_net(state).max(1)[1].view(1, 1).item())*2
#            if action != prev:
#                print("Msg=", i, " Action=", action)
#                prev = action
#            
            #if key not in adict.keys():
            #    adict[key] = 0
            #else:
            #    adict[key] += 1

    #print(adict)
    
#runNetpipe2("tmp.log")

s = pd.Series(np.random.randn(5), index=['a', 'b', 'c', 'd', 'e'])
print(s)
