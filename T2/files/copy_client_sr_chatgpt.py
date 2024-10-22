#!/usr/bin/python3

import jsockets
import sys, threading, time

# Error handling for arguments
if len(sys.argv) != 5:
    print('Use: ' + sys.argv[0] + ' pack_sz win host port', file=sys.stderr)
    sys.exit(1)

# Mutex and conditions
mutex = threading.Lock()
cond = threading.Condition()

# Input variables
pack_sz = int(sys.argv[1]) - 2
win = int(sys.argv[2])
host = sys.argv[3]
port = int(sys.argv[4])

# Initial timeout and RTT
timeout = 0.5
rtt = timeout

# Counters
num_retransmissions = 0
num_out_of_order = 0

# Sequence number variables
seq_num = 0
seq_base = 0
seq_max = win + 1

# Windows
send_window = [None] * win
receive_window = [None] * win

# Status flags
all_data_sent = False
all_data_received = False

# Adaptative timeout function
def adapt_timeout(rtt):
    return rtt * 3

# Sender thread
def Sender(s):
    global num_retransmissions, all_data_sent, seq_num, rtt

    while True:
        data = sys.stdin.buffer.read(pack_sz)
        if not data:
            # Send an empty packet to signal the end of transmission
            with cond:
                empty_packet = seq_num.to_bytes(2, 'big')
                s.send(empty_packet)
                all_data_sent = True
                cond.notify_all()
            break

        # Build packet with sequence number
        packet = seq_num.to_bytes(2, 'big') + data
        
        with cond:
            # Send packet and save in the window
            s.send(packet)
            send_window[seq_num % win] = packet
            start_time = time.time()

            # Wait until the window has space
            while seq_num >= seq_base + win:
                cond.wait()

            # Update sequence number
            seq_num = (seq_num + 1) % 65536

            # Adaptive RTT for retransmission timeout
            rtt = adapt_timeout(time.time() - start_time)

# Receiver thread
def Receiver(s):
    global num_out_of_order, all_data_received, seq_base

    expected_seq = 0

    while True:
        data = s.recv(pack_sz + 2)
        if not data:
            break

        # Extract sequence number and packet data
        seq_num_received = int.from_bytes(data[:2], 'big')
        packet_data = data[2:]

        with cond:
            # If empty packet is received and it's the expected sequence, we are done
            if not packet_data and seq_num_received == expected_seq:
                all_data_received = True
                cond.notify_all()
                break

            # If the received packet is in order, write to stdout
            if seq_num_received == expected_seq:
                sys.stdout.buffer.write(packet_data)
                expected_seq = (expected_seq + 1) % 65536

                # Write any packets already in the receive window
                while receive_window[expected_seq] is not None:
                    sys.stdout.buffer.write(receive_window[expected_seq])
                    receive_window[expected_seq] = None
                    expected_seq = (expected_seq + 1) % 65536

            # If the packet is out of order, store it in the receive window
            elif seq_num_received > expected_seq:
                receive_window[seq_num_received % win] = packet_data
                num_out_of_order += 1

            # Notify sender to adjust the base of the window
            seq_base = expected_seq
            cond.notify_all()

# Connection setup
s = jsockets.socket_udp_connect(host, port)
if s is None:
    print('Could not open socket', file=sys.stderr)
    sys.exit(1)

# Start the sender and receiver threads
sender_thread = threading.Thread(target=Sender, args=(s,))
receiver_thread = threading.Thread(target=Receiver, args=(s,))

sender_thread.start()
receiver_thread.start()

# Wait for threads to finish
sender_thread.join()
receiver_thread.join()

# Final stats and closing
print('Using: pack_sz:', pack_sz + 2, 'maxwin:', win, file=sys.stderr)
print('Send errors:', num_retransmissions, file=sys.stderr)
print('Receive errors:', num_out_of_order, file=sys.stderr)

# Close connection
s.close()

