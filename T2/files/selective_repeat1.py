#!/usr/bin/python3
import jsockets
import sys
import threading
import time

# Error handling
if len(sys.argv) != 5:
    print('Use: ' + sys.argv[0] + ' pack_sz win host port', file=sys.stderr)
    sys.exit(1)

# Mutex and conditions
mutex = threading.Lock()
condition = threading.Condition()

# Input variables
pack_sz = int(sys.argv[1]) - 2  # 2 bytes for sequence number
win = int(sys.argv[2])
host = sys.argv[3]
port = int(sys.argv[4])

# Initial timeout
timeout = 0.5

# Counters
num_retransmissions = 0
num_out_of_order = 0

# Windows
send_window = [None] * win
acked_packets = [False] * win
base = 0  # Sequence number of the base of the sending window
seq_num = 0  # Next sequence number to send

# Function to receive packets
def Rdr(s):
    global base, num_out_of_order
    while True:
        data = s.recv(pack_sz + 2)
        if not data:
            print("No more data, exiting receiver", file=sys.stderr)
            break
        
        seq_num_received = int.from_bytes(data[:2], 'big')

        # Check if the packet is in the receiving window
        if base <= seq_num_received < base + win:
            acked_packets[seq_num_received % win] = True  # Mark packet as acknowledged
            print(f"Received ACK for packet {seq_num_received}", file=sys.stderr)
        else:
            num_out_of_order += 1  # Packet outside the window
            break

        # If the acknowledged packet is the base, slide the window
        while acked_packets[base % win]:
            acked_packets[base % win] = False
            base += 1

# Connection
s = jsockets.socket_udp_connect(host, port)
if s is None:
    print('Could not open socket', file=sys.stderr)
    sys.exit(1)

# Receiver thread
reader_thread = threading.Thread(target=Rdr, args=(s,))
reader_thread.start()

# Read file to data chunks list
file_data = sys.stdin.buffer.read()
data_chunks = [file_data[i:i + pack_sz] for i in range(0, len(file_data), pack_sz)]

# Sending packets
print("Start sending", file=sys.stderr)

while seq_num < len(data_chunks):
    while seq_num < base + win and seq_num < len(data_chunks):
        # Prepare the packet
        packet_data = data_chunks[seq_num]
        packet = seq_num.to_bytes(2, 'big') + packet_data

        # Send the packet
        with mutex:
            s.send(packet)
            send_window[seq_num % win] = packet
            print(f"Sent packet {seq_num}", file=sys.stderr)

        seq_num += 1

    # Wait for ACKs or timeout
    start_time = time.time()
    while base < seq_num:
        with condition:
            elapsed_time = time.time() - start_time
            if elapsed_time >= timeout:
                print("Timeout! Resending unacknowledged packets...", file=sys.stderr)
                num_retransmissions += 1
                for i in range(base, seq_num):
                    if send_window[i % win] is not None:
                        s.send(send_window[i % win])
                        print(f"Retransmitted packet {i}", file=sys.stderr)
                start_time = time.time()

            condition.wait(timeout - elapsed_time)

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

# Closing connection
s.close()
