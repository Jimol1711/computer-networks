#!/usr/bin/python3

import jsockets
import sys
import threading
import time

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

# Counters
num_retransmissions = 0
num_out_of_order = 0

# variables
N = win
Rn = 0
Sn = 0
Sb = 0
Sm = 0

# Windows
send_window = [False] * N
receive_window = [False] * N
buffer = [False] * N

# Adaptative timeout function
def adapt_timeout(rtt):
    return rtt * 3

# Sender thread
def Sender(s):

    global Sb, Sm, buffer, Sn, Rn, N, timeout, num_retransmissions

    with mutex:
        Sb = 0
        Sm = N + 1
        buffer = [None] * N  # Buffer to hold packets or None for empty slots
        Sn = 0  # Initial sequence number
        Rn = 0  # Request number initially 0

    while True:
        # Check if we received a request number greater than Sb
        if Rn > Sb:
            with mutex:
                Sb = Rn
                Sm = Sb + N

                # Remove packets from buffer with sequence numbers < Rn
                for i in range(len(buffer)):
                    if buffer[i]:
                        seq_num_on_buffer = int.from_bytes(buffer[i][:2], 'big')
                        if seq_num_on_buffer < Rn:
                            buffer[i] = None  # Clear packet from buffer

        # Read new data from stdin
        data = sys.stdin.buffer.read(pack_sz)
        if not data:
            break  # End of input

        packet = Sn.to_bytes(2, 'big') + data  # Packet includes sequence number

        with cond:
            # Check if Sn is within the send window
            if Sb <= Sn < Sm:
                start_time = time.time()  # Start timer for timeout
                s.send(packet)  # Send the packet
                print("Sending packet", Sn, file=sys.stderr)

                # Store the packet in the buffer (for retransmission if needed)
                buffer[Sn % N] = packet

                # Wait for the condition (ACK or timeout)
                if not cond.wait(timeout):  # Wait with timeout
                    print(f"Timeout occurred for packet {Sn}", file=sys.stderr)
                    # Timeout logic will trigger retransmission later

                Sn += 1  # Increment sequence number

        # Retransmission logic
        for i in range(len(buffer)):
            if buffer[i]:  # Packet exists in buffer
                # Check if the packet has timed out
                if time.time() - start_time >= timeout:
                    s.send(buffer[i])  # Retransmit packet
                    print("Retransmitting packet", i, file=sys.stderr)
                    start_time = time.time()  # Reset the timer after retransmission
                    num_retransmissions += 1  # Increment retransmission counter

        # Update RTT and timeout based on successful transmissions
        with mutex:
            rtt = time.time() - start_time
            timeout = adapt_timeout(rtt)
   
# Receiver thread
def Receiver(s):

    global Rn, buffer

    with mutex:
        Rn = 0  # Initialize Rn (expected sequence number)
        buffer = [None] * N  # Initialize buffer with None for empty slots

    while True:
        # Receive packet
        data = s.recv(pack_sz + 2)  # Includes 2 bytes for sequence number
        if not data:
            print("Received last packet", file=sys.stderr)
            break  # Exit the loop if the connection is closed (or an empty packet is received)

        # Extract sequence number and packet data
        seq_num_received = int.from_bytes(data[:2], 'big')
        packet_data = data[2:]

        if seq_num_received == Rn:
            # Expected packet, write it to stdout
            sys.stdout.buffer.write(packet_data)
            Rn = (Rn + 1) % 65536  # Update Rn to expect the next packet

            # Process any buffered packets that are in order
            with mutex:
                while buffer[Rn % N]:
                    sys.stdout.buffer.write(buffer[Rn % N][2:])  # Write the buffered data
                    buffer[Rn % N] = None  # Mark buffer slot as empty
                    Rn = (Rn + 1) % 65536  # Move to the next expected packet

        elif seq_num_received > Rn:
            # Out-of-order packet, store it in the buffer
            with mutex:
                buffer[seq_num_received % N] = data  # Buffer the packet for later

        else:
            # Received an already processed packet, likely a retransmission (ignore)
            continue

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

