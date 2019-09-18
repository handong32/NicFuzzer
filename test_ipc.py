import sys
import sysv_ipc

try: 
    mq = sysv_ipc.MessageQueue(0x4797d6b7)
    #mq = sysv_ipc.MessageQueue(None, sysv_ipc.IPC_CREX)
    message = mq.receive()
    print("Received", float(message[0]))
except Exception as e:
    print("ERROR: message queue creation failed", e) 
