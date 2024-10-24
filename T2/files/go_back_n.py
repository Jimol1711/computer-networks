#!/usr/bin/python3
# Echo client program
# Version with two threads: one reads from stdin to the socket and the other does the reverse
import jsockets
import sys
import threading
import time

# Error handling
if len(sys.argv) != 5:
    print('Use: ' + sys.argv[0] + ' pack_sz win host port', file=sys.stderr)
    sys.exit(1)

# Mutex and condition variables
mutex = threading.Lock()
condition = threading.Condition(mutex)

# Input variables
pack_sz = int(sys.argv[1]) - 2
win = int(sys.argv[2])
host = sys.argv[3]
port = int(sys.argv[4])

# Sliding window variables
seq_base = 0
seq_num = 0
timeout = 0.5
unacked_packets = {}

# Flags for final packet acknowledgment
final_packet_sent = False
final_packet_acked = False
terminate_program = False

# counters
num_retransmissions = 0
num_out_of_order = 0

# Receiver function
def Rdr(s):
    global seq_base, final_packet_acked, terminate_program
    while True:
        data = s.recv(pack_sz + 2)
        
        if not data:
            print("No more data, exiting receiver", file=sys.stderr)
            break

        # Sequence number and data
        seq_num_received = int.from_bytes(data[:2], 'big')
        packet_data = data[2:]

        with mutex:
            if seq_num_received >= seq_base:  # Process only if it's in the valid range
                if packet_data == b'':  # Empty packet indicates end
                    final_packet_acked = True
                    terminate_program = True
                    condition.notify_all()
                    break

                sys.stdout.buffer.write(packet_data)
                
                # Update base if received in order
                if seq_num_received == seq_base:
                    seq_base += 1
                    # Notify other threads
                    condition.notify_all()
                # Optionally handle out-of-order packets

s = jsockets.socket_udp_connect(host, port)
if s is None:
    print('Could not open socket', file=sys.stderr)
    sys.stdout.flush()
    sys.exit(1)

# Start the receiver thread
reader_thread = threading.Thread(target=Rdr, args=(s,))
reader_thread.start()

# Function to resend unacknowledged packets
def resend_unacked_packets():
    with mutex:
        print("Timeout! Resending unacknowledged packets from", seq_base, file=sys.stderr)
        for sn in range(seq_base, seq_num):
            if sn in unacked_packets:
                s.sendto(unacked_packets[sn], (host, port))
                print(f"Retransmitting packet {sn}", file=sys.stderr)
                sys.stdout.flush()

# Main sending loop
while not terminate_program:
    with mutex:
        # Send packets while within window limits
        while seq_num < seq_base + win:
            chunk = sys.stdin.buffer.read(pack_sz)
            if chunk == b'':  # EOF
                final_packet_sent = True
                seq_num_bytes = seq_num.to_bytes(2, 'big')
                packet = seq_num_bytes + b''  # Empty packet to signal end
                s.sendto(packet, (host, port))
                unacked_packets[seq_num] = packet
                print(f"Sent final empty packet {seq_num}", file=sys.stderr)
                seq_num += 1
                break  # Exit the loop to allow final packet handling

            seq_num_bytes = seq_num.to_bytes(2, 'big')
            packet = seq_num_bytes + chunk
            s.sendto(packet, (host, port))
            unacked_packets[seq_num] = packet
            print(f"Sent packet {seq_num}", file=sys.stderr)
            seq_num += 1

    # Start the timer for unacknowledged packets
    start_time = time.time()

    with condition:
        while seq_base == 0 or (seq_num > seq_base and not terminate_program):
            elapsed_time = time.time() - start_time
            if elapsed_time >= timeout:
                resend_unacked_packets()
                start_time = time.time()
            condition.wait(timeout - elapsed_time)

# Final acknowledgment wait
with condition:
    while not final_packet_acked and not terminate_program:
        elapsed_time = time.time() - start_time
        if elapsed_time >= timeout:
            resend_unacked_packets()
            start_time = time.time()
        condition.wait(timeout - elapsed_time)

# Wait for the receiver thread to finish
reader_thread.join()

# print statistics
print('Using: pack:', pack_sz, 'maxwin:', win, file=sys.stderr)
print('Send errors:', num_retransmissions, file=sys.stderr)
print('Receive errors:', num_out_of_order, file=sys.stderr)
s.close()