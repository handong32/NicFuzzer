import zmq

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect ("tcp://localhost:5563")
socket.setsockopt( zmq.LINGER, 0 ) 
socket.setsockopt( zmq.SUBSCRIBE, "" )

while True:
    print(float(socket.recv()))
