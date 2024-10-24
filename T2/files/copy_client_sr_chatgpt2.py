#!/usr/bin/python3
import jsockets
import sys, threading, time

# error handling
if len(sys.argv) != 5:
    print('Use: ' + sys.argv[0] + ' pack_sz win host port', file=sys.stderr)
    sys.exit(1)

# mutex
mutex = threading.Lock()
condition = threading.Condition(mutex)
condition2 = threading.Condition()

# input variables
pack_sz = int(sys.argv[1]) - 2  # 2 bytes for seq num
win = int(sys.argv[2])
host = sys.argv[3]
port = int(sys.argv[4])

# initial timeout
timeout = 0.5

# counters
num_retransmissions = 0
num_out_of_order = 0

# windows
send_window = [None] * win
receive_window = [None] * win
base = 0  # seq num of the base of the sending window
recv_base = 0  # seq num of the base of the receiving window
seq_num = 0  # expected seq num in the receiving window
next_seq_num = 0

# Helper functions
def adapt_timeout(rtt):
    return rtt * 3

# function to receive packets
def Rdr(s):
    global num_out_of_order, expected_seq, recv_base

    while True:
        print("entering while rec", file=sys.stderr)
        print("entering while rec asdsa", file=sys.stderr)
        data = s.recv(pack_sz + 2)
        print("entering while rec asdswdadwaa", file=sys.stderr)

        seq_num_received = int.from_bytes(data[:2], 'big')
        packet_data = data[2:]

        print(seq_num_received, file=sys.stderr)

        if not packet_data:
            print("No more data, exiting receiver", file=sys.stderr)
            break

        print(seq_num_received, file=sys.stderr)
        print(packet_data.decode(), file=sys.stderr)

        mutex.acquire()
        if recv_base <= seq_num_received < recv_base + win:
            # In-order packet
            if seq_num_received == expected_seq:
                sys.stdout.buffer.write(packet_data)  # Output the packet content
                expected_seq += 1
            else:
                # Out-of-order packet
                num_out_of_order += 1
                receive_window[seq_num_received % win] = packet_data  # Buffering the packet
            recv_base = min(recv_base + 1, 65535)
        else:
            # Packet outside the receiving window, discard
            num_out_of_order += 1
        mutex.release()

        print("infinite loop 2?", file=sys.stderr)
        # Exit condition: received an empty packet, and all in-order packets are received
        if not packet_data: # and expected_seq == recv_base:
            break

# connection
s = jsockets.socket_udp_connect(host, port)
if s is None:
    print('Could not open socket', file=sys.stderr)
    sys.exit(1)

# receiver thread
reader_thread = threading.Thread(target=Rdr, args=(s,))
reader_thread.start()

# read file to data chunks list
file_data = sys.stdin.buffer.read()  # Read file input
data_chunks = [file_data[i:i+pack_sz] for i in range(0, len(file_data), pack_sz)]

# class to create a packet to send
class Packet:
    def __init__(self, seq_num, data):
        self.seq_num = seq_num  # Sequence number
        self.data = data  # Data payload
        self.start_time = time.time()  # Timestamp when packet was created
        self.acked = False # Acked flag

def send_packet():
    global next_seq_num, seq_num
    # Prepare the packet
    packet_data = data_chunks[next_seq_num]
    packet = seq_num.to_bytes(2, 'big') + packet_data

    packet_obj = Packet(next_seq_num, packet)

    # Send the packet
    s.send(packet)
    print(f"Sent packet {seq_num}", file=sys.stderr)
    send_window[next_seq_num % win] = packet_obj

    next_seq_num += 1
    seq_num = (seq_num + 1) % 65536
    return packet_obj

print("Start sending", file=sys.stderr)

while next_seq_num < len(data_chunks) and next_seq_num < base + win:
    print("Sending in progress...", file=sys.stderr)
    # Wait until there's space in the window
    with mutex:
        # sending packet
        send_packet()

# Window is filled, now wait for ACK of the first packet (or retransmit on timeout)
print(f"Window filled, waiting for ACK for seq_num {seq_num}", file=sys.stderr)
        
# Wait for the first packet in the window to be acknowledged
while not receive_window[base % win]:
    with condition:
        # Wait for either an ACK to arrive or timeout
        if not condition.wait(timeout):
            # Timeout occurred, so retransmit the entire window
            print("Timeout! Retransmitting window...", file=sys.stderr)
            
            with mutex:
                for i in range(base, base + win):
                    if i < len(data_chunks) and send_window[i % win]:
                        resend_packet = send_window[i % win]
                        if not resend_packet.acked:
                            s.send(resend_packet.data)
                            print(f"Retransmitted packet {resend_packet.seq_num}", file=sys.stderr)

# Slide the window forward
with mutex:
    receive_window[base % win] = None  # Clear the acknowledged packet
    base += 1  # Move the base of the window forward

# Once the first packet has been acknowledged:
print(f"Packet with sequence number {seq_num} acknowledged.", file=sys.stderr)

# Sending final empty packet
final_packet = seq_num.to_bytes(2, 'big')  # Empty data
s.send(final_packet)
print(f"Sent final packet with seq_num {seq_num}", file=sys.stderr)

# Wait for reader thread to finish
reader_thread.join()

# Print final statistics
print('Using: pack_sz:', pack_sz + 2, 'maxwin:', win, file=sys.stderr)
print('Send errors:', num_retransmissions, file=sys.stderr)
print('Receive errors:', num_out_of_order, file=sys.stderr)

# closing connection
s.close()
