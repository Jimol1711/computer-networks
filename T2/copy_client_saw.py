#!/usr/bin/python3
# Echo client program using UDP with Stop-and-Wait protocol
import jsockets
import sys
import threading
import time

# Shared memory variables
lock = threading.Lock()
send_window = []        # Sender's window to keep track of sent packets
received_window = []    # Receiver's window to keep track of received packets
total_sent_bytes = 0
seq_num = 0
window_size = 1  # Stop-and-Wait means window size of 1
timeout = 1  # Timeout for retransmission

# Receiver thread function
def Rdr(s, total_bytes):
    global total_sent_bytes
    received_bytes = 0

    while received_bytes < total_bytes:
        try:
            data, addr = s.recvfrom(pack_sz + 2)  # Adjusted for sequence number
            if not data:
                break

            # Extract the sequence number from the first 2 bytes
            seq_num_received = int.from_bytes(data[:2], 'big')
            packet_data = data[2:]  # Extract actual data without sequence number

            with lock:
                # Process the received packet
                sys.stdout.buffer.write(packet_data)
                received_bytes += len(packet_data)

                # Store the received packet's seq_num in the received window
                if seq_num_received not in received_window:
                    received_window.append(seq_num_received)

                # Remove acknowledged packets from send_window if they are received
                if send_window and send_window[0][0] == seq_num_received:
                    send_window.pop(0)  # Remove the acknowledged packet

        except Exception as e:
            print("Error receiving data:", str(e))
            break

# Command-line argument handling
if len(sys.argv) != 5:
    print('Use: ' + sys.argv[0] + ' pack_sz win host port')
    sys.exit(1)

pack_sz = int(sys.argv[1]) - 2  # Subtract 2 bytes for sequence number
window_size = int(sys.argv[2])  # In Stop-and-Wait, this should be 1
host = sys.argv[3]
port = int(sys.argv[4])

# Establish UDP connection
s = jsockets.socket_udp_connect(host, port)
if s is None:
    print('Could not open socket')
    sys.exit(1)

# Read input data in chunks
total_bytes = 0
input_data_chunks = []
while True:
    chunk = sys.stdin.buffer.read(pack_sz)
    if not chunk:
        break
    input_data_chunks.append(chunk)
    total_bytes += len(chunk)

# Create a thread to receive data from the server and write to stdout
reader_thread = threading.Thread(target=Rdr, args=(s, total_bytes))
reader_thread.start()

# Sending thread - adding sequence number and sending chunks
sent_bytes = 0

for chunk in input_data_chunks:
    while True:
        with lock:
            # Prepare the data with sequence number
            data_with_seq = seq_num.to_bytes(2, 'big') + chunk
            s.sendto(data_with_seq, (host, port))  # Send packet
            send_window.append((seq_num, data_with_seq))  # Track sent packet with its sequence number
            print(f"Sent packet seq_num: {seq_num}")

        # Wait for the receiver to process the packet
        start_time = time.time()

        while True:
            with lock:
                # Check if the packet has been processed by the receiver
                if seq_num in received_window:
                    print(f"Packet seq_num {seq_num} received by receiver.")
                    seq_num = (seq_num + 1) % 65536  # Increment sequence number
                    break

            # Timeout check
            if time.time() - start_time > timeout:
                print(f"Timeout, resending packet seq_num: {seq_num}")
                break  # Break the inner loop to resend the packet

        time.sleep(0.01)  # Short sleep to avoid busy waiting

# Wait for the reader thread to finish
reader_thread.join()

# Print statistics
print(f'Sent: {total_sent_bytes} bytes, Pack size: {pack_sz + 2}, Total chunks: {len(input_data_chunks)}')
s.close()
