import sys
import sysv_ipc

try: 
    mq = sysv_ipc.MessageQueue(0x4797d6b7)
    mq.send("abcccc", True)
except Exception as e:
    print("ERROR: message queue creation failed", e) 

    
