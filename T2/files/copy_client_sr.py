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
import sys, threading, time

# error handling
if len(sys.argv) != 5:
    print('Use: ' + sys.argv[0] + ' pack_sz win host port', file=sys.stderr)
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

# retransmission and out of order counters
num_retransmissions = 0
num_out_of_order = 0

# seq num variables
req_num = 0
seq_num = 0
seq_base = 0
seq_max = win + 1

# windows
send_window = [None] * win
receive_window = [None] * win

# ADDED
send_timers = [None] * win  # To store timers for each packet
# ENDADDED

# ADDED
# status flags for stop condition
all_data_sent = False
all_data_received = False
# ENDADDED

# adaptative timeout
def adapt_timeout(rtt):
    """
    Return rtt given multiplied by 3
    :param rtt:= rtt value given to the function
    """
    return rtt * 3

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

# ADDED
# Sender thread logic
"""
def Sender(s):

    global num_retransmissions, all_data_sent

    seq_num = 0
    rtt = timeout

    while True:
        # Read data from stdin (file or user input)
        data = sys.stdin.buffer.read(pack_sz)
        if not data:
            # Send an empty packet to signal the end of data transmission
            empty_packet = seq_num.to_bytes(2, 'big')
            s.send(empty_packet)
            all_data_sent = True
            # final stats and closing
            print('Empty packet seq num:', seq_num, file=sys.stderr)
            print('Using: pack_sz:', pack_sz + 2, 'maxwin:', win, file=sys.stderr)
            print('Send errors:', num_retransmissions, file=sys.stderr)
            print('Receive errors:', num_out_of_order, file=sys.stderr)
            break

        # Build the packet: seq_num + data
        packet = seq_num.to_bytes(2, 'big') + data

        # Send the packet
        s.send(packet)
        start_time = time.time()

        # Start a timer for the packet
        with mutex:
            send_window[seq_num % win] = packet
            send_timers[seq_num % win] = start_time

        # Increment sequence number, wrapping at 65535
        seq_num = (seq_num + 1) % 65536

        # Wait for an adaptive timeout before sending the next packet
        rtt = adapt_timeout(time.time() - start_time)
        time.sleep(rtt)
"""
# ENDADDED

# ADDED
"""
# Receiver thread logic
def Receiver(s):
    global num_out_of_order, all_data_received

    expected_seq = 0

    while True:
        # Receive packet from the socket
        data = s.recv(pack_sz + 2)
        if not data:
            print("No more data, exiting receiver", file=sys.stderr)
            break

        # Extract sequence number and data
        seq_num_received = int.from_bytes(data[:2], 'big')
        packet_data = data[2:]

        with mutex:
            # Check if the packet is in the correct order
            if seq_num_received == expected_seq:
                sys.stdout.buffer.write(packet_data)
                expected_seq = (expected_seq + 1) % 65536
            else:
                num_out_of_order += 1

        # If the packet is empty and it's the expected sequence number, we are done
        if not packet_data and seq_num_received == expected_seq:
            all_data_received = True
            # final stats and closing
            print('Using: pack_sz:', pack_sz + 2, 'maxwin:', win, file=sys.stderr)
            print('Send errors:', num_retransmissions, file=sys.stderr)
            print('Receive errors:', num_out_of_order, file=sys.stderr)
            break
"""
# ENDADDED

# receiver thread
def Receiver(s):

    global req_num, receive_window, num_out_of_order

    # selective repeat logic for receiver thread
    while True:
        data = s.recv(pack_sz + 2)        
        
        if not data:
            print("Error: no data", file=sys.stderr)
            break

        # seq num and data
        seq_num_received = int.from_bytes(data[:2], 'big')
        packet_data = data[2:]

        if not packet_data:
            print("final packet received", file=sys.stderr)
            # Aquí implementar lo que pasa cuando faltan paquetes por recibir en la ventana
            break

        if seq_num_received == req_num:
            sys.stdout.buffer.write(packet_data)
            req_num += 1

            while receive_window[req_num] is not None:
                sys.stdout.buffer.write(receive_window[req_num])
                receive_window[req_num] = None
                req_num += 1

        elif seq_num_received > req_num:
            receive_window[seq_num_received] = packet_data
            num_out_of_order += 1

        else:
            num_out_of_order += 1
            continue

    return

# sender thread
def Sender(s):
    
    global req_num, seq_base, seq_max, receive_window, num_retransmissions, num_out_of_order
    
    while True:
        # HERE SHOULD BE IMPLEMENTED LOGIC FOR SENDER THREAD
        if req_num > seq_base:
            seq_max = (seq_max - seq_base) + req_num
            seq_base = req_num
        
            # Remove packets with Sn < Rn from the buffer
            for i in range(0, len(receive_window)):
                seq_num_packet = int.from_bytes(receive_window[i][:2], 'big') if receive_window[i] is not None else -1
                if seq_num_packet != -1:
                    receive_window[i] = None
                else:
                    continue
                
    return

# connection
s = jsockets.socket_udp_connect(host, port)
if s is None:
    print('Could not open socket', file=sys.stderr)
    sys.exit(1)

# starting threads
sender_thread = threading.Thread(target=Sender, args=(s,))
sender_thread.start()

receiver_thread = threading.Thread(target=Receiver, args=(s,))
receiver_thread.start()

sender_thread.join()
receiver_thread.join()

# final stats and closing
print('Using: pack_sz:', pack_sz + 2, 'maxwin:', win, file=sys.stderr)
print('Send errors:', num_retransmissions, file=sys.stderr)
print('Receive errors:', num_out_of_order, file=sys.stderr)

# closing connection
s.close()