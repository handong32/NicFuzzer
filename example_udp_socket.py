import socket
import sys

UDP_IP = "192.168.1.230"
UDP_PORT = 6666
MESSAGE = str(sys.argv[1]) 
#"rx_usecs,20"

#print "UDP target IP:", UDP_IP
#print "UDP target port:", UDP_PORT
#print "message:", MESSAGE

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))

#if MESSAGE == "get":
#    data, addr = sock.recvfrom(4096) # buffer size is 1024 bytes
#    print data
