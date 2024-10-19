#!/usr/bin/python3
# Echo client program
# Version with two threads: one reads from stdin to the socket and the other does the reverse

# MANDATORY THINGS
# 1. DOES NOT use ACKs
# synchronization is handled through shared memory
# Receiver and sender can see each other windows but with mutexes and conditions

# 2. timeout MUST be adaptative:
# it starts as 0.5. Then rtt must be calculated for each

# 3. packets are sent with sequence number at the beginning
# sequence number is added with native function int.to_bytes() and int.from_bytes()
# therefore, pack_sz is defined as (pack_sz - 2) to include 2 bytes for seq num.
# seq nums go from 0 to 65535.
# window size goes from 1 to 32767

# 4. Since it is UDP, there is no connection closing.
# Therefore, when there is no more data, a final empty packet must be sent with only seq number
# the entire program ends once that packet is received AND all other packets as well(including
# previous one that haven't arrived and are out of order) In other words,the program only ends 
# once the empty package leaves the receiving window.

# 5. It must print errors at the end.
# There are two types of errors:
# 1) Sending errors: any retransmission.
# 2) Receiving errors: out of order packages (Both inside the receiving window and packets
# received outside of it).
# Counters must be updated througout the program and printed at the end when it closes.

# Example execution would be (with server_echo_udp.py running on host 127.0.0.1 port 1818):
# % ./copy_client.py 8000 10000 127.0.0.1 1818 < filein > fileout
# Using: pack_sz: 8000, maxwin: 10000
# Send errors: 2
# Receive errors: 2
# And the fileout file should be created with the exact same content as filein

# jsockets.py module is as follows
# jsockets.py:
"""
# jsockets para Python3
# sería bonito tener soporte para multicast
import socket
import sys

# accept no aporta nada en realidad...
def accept(s):
    return s.accept()

def socket_tcp_bind(port):
    return socket_bind(socket.SOCK_STREAM, port)

def socket_udp_bind(port):
    return socket_bind(socket.SOCK_DGRAM, port)

def socket_bind(type, port):
    s = None
    for res in socket.getaddrinfo(None, port, socket.AF_UNSPEC, type, 0, socket.AI_PASSIVE):
        af, socktype, proto, canonname, sa = res
        try:
            s = socket.socket(af, socktype, proto)
        except socket.error as msg:
            s = None
            continue
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if(type == socket.SOCK_DGRAM):
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                # s.setsockopt(socket.IPPROTO_IP, socket.IP_MTU_DISCOVER, 0) Para Linux?
            s.bind(sa)
            if(type == socket.SOCK_STREAM):
                s.listen(5)
        except socket.error as msg:
            s.close()
            s = None
            print(msg)
            break
        break

    return s

def socket_tcp_connect(server, port):
    return socket_connect(socket.SOCK_STREAM, server, port)

def socket_udp_connect(server, port):
    return socket_connect(socket.SOCK_DGRAM, server, port)

#def socket_udp_unconnect(s):
#    return s.connect((0, 0)) # no funciona con '' ni None ni 0

def socket_connect(type, server, port):
    s = None
    for res in socket.getaddrinfo(server, port, socket.AF_UNSPEC, type):
        af, socktype, proto, canonname, sa = res
        try:
            s = socket.socket(af, socktype, proto)
        except socket.error as msg:
            s = None
            continue
        try:
            s.connect(sa)
        except socket.error as msg:
            s.close()
            s = None
            continue
        break

    return s
"""
    
# Server where data will 'bounce' is as follows
# server_echo_udp.py:
"""
#!/usr/bin/python3
# Echo server UDP program - version of server_echo_udp.c, mono-cliente
import jsockets
import sys # Se importó el módulo sys que no estaba importado

s = jsockets.socket_udp_bind(1818)
if s is None:
    print('could not open socket')
   sys.exit(1)
print('Server is running on port 1818')

while True:
    # Se modificó el servidor para que reciba 1024 * 1024 bytes
    data, addr = s.recvfrom(1024*1024)
    if not data: break
    s.sendto(data, addr)

s.close()
"""

# Selective Repeat
import jsockets
import sys, threading
import time

# error handling
if len(sys.argv) != 5:
    print('Use: ' + sys.argv[0] + ' pack_sz win host port')
    sys.stdout.flush()
    sys.exit(1)

# mutex
mutex = threading.Lock()
condition = threading.Condition(mutex)

# input variables
pack_sz = int(sys.argv[1]) - 2
win = int(sys.argv[2])
host = sys.argv[3]
port = int(sys.argv[4])

# initial timeout
timeout = 0.5

# adaptative timeout
def adapt_timeout(rtt):
    return rtt * 3

# retransmission and out of order counters
num_retransmissions = 0
num_out_of_order = 0

# windows
send_window = [None] * win
receive_window = [None] * win

# function to adapt window
def adapt_window(window, new_element):
    """ 
    Shifts the window to the left and add the new packet at the end 
    :param window:= list representing the window
    :param new_element:= element to add at the end of the window
    """
    window.pop(0)
    window.append(new_element)
    return window

# function to receive packets
def Rdr(s):

    # HERE SHOULD BE IMPLEMENTED LOGIC FOR RECEIVER THREAD
    while True:
        data = s.recv(pack_sz + 2)        
        
        if not data:
            print("No more data, exiting receiver")
            break

        # seq num and data
        seq_num_received = int.from_bytes(data[:2], 'big')
        packet_data = data[2:]

    return

# connection
s = jsockets.socket_udp_connect(host, port)
if s is None:
    print('Could not open socket')
    sys.exit(1)

# receiver thread
reader_thread = threading.Thread(target=Rdr, args=(s,))
reader_thread.start()

# sender thread (main)
while True:
    # HERE SHOULD BE IMPLEMENTED LOGIC FOR SENDER THREAD
    break

reader_thread.join()

# final stats and closing
print('Using: pack_sz:', pack_sz + 2, 'maxwin:', win)
print('Send errors:', num_retransmissions)
print('Receive errors:', num_out_of_order)
sys.stdout.flush()

# closing connection
s.close()