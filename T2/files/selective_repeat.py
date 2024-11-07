#!/usr/bin/python3
import jsockets
import sys, threading, time

# Error handling
if len(sys.argv) != 5:
    print('Use: ' + sys.argv[0] + ' pack_sz win host port', file=sys.stderr)
    sys.exit(1)

# Mutex and condition variables for shared memory control
mutex = threading.Lock()
condition = threading.Condition(mutex)

# Input arguments
pack_sz = int(sys.argv[1]) - 2  # 2 bytes for sequence number
win = int(sys.argv[2])
host = sys.argv[3]
port = int(sys.argv[4])

# Timeout for retransmission
timeout = 0.5

# Counters for retransmissions and out-of-order packets
num_retransmissions = 0
num_out_of_order = 0

# Shared memory for the sliding windows
send_window = [None] * win
receive_window = [False] * win  # Track if packet was received in window
send_base = 0  # Base of the sending window
recv_base = 0  # Base of the receiving window
next_seq_num = 0

# Shared variables to manage end of transmission
transmission_done = False
end_signal_received = False  # Receiver sets this when empty packet is received

# File input data
file_data = sys.stdin.buffer.read()  # Read file input
data_chunks = [file_data[i:i + pack_sz] for i in range(0, len(file_data), pack_sz)]
total_packets = len(data_chunks)

# Class for packet management
class Packet:
    def __init__(self, seq_num, data):
        self.seq_num = seq_num
        self.data = data
        self.timestamp = time.time()  # When the packet was sent

# Function to handle sending packets
def send_packet():
    global next_seq_num, send_base
    # Sending only inside the window
    if next_seq_num < send_base + win and next_seq_num < total_packets:
        # Prepare the packet
        packet_data = next_seq_num.to_bytes(2, 'big') + data_chunks[next_seq_num]
        packet_obj = Packet(next_seq_num, packet_data)

        # Send the packet
        s.send(packet_data)
        print(f"Sent packet {next_seq_num}", file=sys.stderr)
        send_window[next_seq_num % win] = packet_obj

        next_seq_num += 1

# Function to handle sending the empty termination packet
def send_termination_packet():
    global next_seq_num
    termination_packet = next_seq_num.to_bytes(2, 'big')  # Empty packet with just sequence number
    s.send(termination_packet)
    print(f"Sent termination packet with seq_num {next_seq_num}", file=sys.stderr)

# Function for the receiver thread to process incoming packets
def receive_packets(s):
    global recv_base, num_out_of_order, transmission_done, end_signal_received

    while True:
        try:
            data = s.recv(pack_sz + 2)
            if not data:
                break

            seq_num_received = int.from_bytes(data[:2], 'big')
            packet_data = data[2:]

            # Lock the shared memory to update received window
            with mutex:
                if len(packet_data) == 0:  # Empty packet signaling end of transmission
                    end_signal_received = True
                    condition.notify_all()
                    print(f"Received termination packet with seq_num {seq_num_received}", file=sys.stderr)
                    break

                if recv_base <= seq_num_received < recv_base + win:
                    # In-order packet
                    if seq_num_received == recv_base:
                        sys.stdout.buffer.write(packet_data)  # Output the packet content
                        receive_window[recv_base % win] = True  # Mark as received
                        recv_base += 1  # Move base forward
                    else:
                        # Out-of-order packet
                        num_out_of_order += 1
                        receive_window[seq_num_received % win] = True  # Mark as received

                condition.notify_all()  # Notify sender thread of received update

        except Exception as e:
            print(f"Receiver error: {e}", file=sys.stderr)
            break

# Function for the sender thread to handle retransmissions and sliding window
def sender():
    global send_base, num_retransmissions, transmission_done, end_signal_received

    while send_base < total_packets:
        with condition:
            send_packet()  # Send new packets as needed

            # Wait for a condition signal or timeout
            if not condition.wait(timeout):
                # Timeout: retransmit all packets in window
                print("Timeout, retransmitting...", file=sys.stderr)
                num_retransmissions += 1

                with mutex:
                    for i in range(send_base, min(send_base + win, total_packets)):
                        if not receive_window[i % win]:  # Only resend unreceived packets
                            s.send(send_window[i % win].data)
                            print(f"Retransmitted packet {i}", file=sys.stderr)

            # Check for received packets and slide the window
            while send_base < total_packets and receive_window[send_base % win]:
                send_base += 1
                receive_window[send_base % win] = False  # Clear the slot

    # After all data packets are sent, send the termination packet
    send_termination_packet()

    # Wait for confirmation that the receiver got the termination packet
    with condition:
        while not end_signal_received:
            condition.wait(timeout)

    print(f"Transmission completed.", file=sys.stderr)

# Setup UDP connection
s = jsockets.socket_udp_connect(host, port)
if s is None:
    print('Could not open socket', file=sys.stderr)
    sys.exit(1)

# Start receiver thread
receiver_thread = threading.Thread(target=receive_packets, args=(s,))
receiver_thread.start()

# Start sender thread
sender()

# Wait for receiver thread to finish
receiver_thread.join()

# Print final statistics
print('Using: pack_sz:', pack_sz + 2, 'maxwin:', win, file=sys.stderr)
print('Retransmissions:', num_retransmissions, file=sys.stderr)
print('Out-of-order packets:', num_out_of_order, file=sys.stderr)

# Close connection
s.close()


