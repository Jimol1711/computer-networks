#!/usr/bin/python3
# Echo client program using UDP with sliding window protocol
import Redes.T2.files.jsockets as jsockets
import sys
import threading
import time

# Shared memory variables
lock = threading.Lock()
send_window = []
total_sent_bytes = 0
seq_num = 0
win = 0
retransmissions = 0  # Counter for retransmissions

# Receiver thread function
def Rdr(s, total_bytes):
    global total_sent_bytes
    global retransmissions
    received_bytes = 0
    last_received = -1

    while received_bytes < total_bytes:
        try:
            data, addr = s.recvfrom(pack_sz + 2)  # Adjusted for sequence number
            if not data:
                break

            # Extract the sequence number from the first 2 bytes using int.from_bytes()
            seq_num_received = int.from_bytes(data[:2], 'big')
            packet_data = data[2:]  # Extract actual data without sequence number

            with lock:
                if seq_num_received == (last_received + 1) % 65536:
                    sys.stdout.buffer.write(packet_data)
                    received_bytes += len(packet_data)
                    last_received = seq_num_received  # Update the last received packet

                # Remove acknowledged packets from send_window
                if send_window and send_window[0][0] == seq_num_received:
                    send_window.pop(0)

        except Exception as e:
            print("Error receiving data:", str(e))
            break

# Command-line argument handling
if len(sys.argv) != 5:
    print('Use: '+sys.argv[0]+' pack_sz win host port')
    sys.exit(1)

pack_sz = int(sys.argv[1]) - 2  # Subtract 2 bytes for sequence number
win = int(sys.argv[2])
host = sys.argv[3]
port = int(sys.argv[4])

# Establish UDP connection
s = jsockets.socket_udp_connect(host, port)
if s is None:
    print('could not open socket')
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
seq_num = 0

for chunk in input_data_chunks:
    while True:
        with lock:
            # Calculate the current size of the send window
            current_win = sum(len(packet) for packet in send_window) + len(chunk) + 2  # +2 for sequence number

            if current_win <= win:  # Check if the total size in bytes is within window size
                # Add sequence number (2 bytes) to the chunk using int.to_bytes()
                data_with_seq = seq_num.to_bytes(2, 'big') + chunk
                s.sendto(data_with_seq, (host, port))
                print(f"Sending packet seq_num: {seq_num} with size: {len(chunk)}")  # Debug print
                send_window.append((seq_num, data_with_seq))  # Track sent packet with its sequence number

                seq_num = (seq_num + 1) % 65536  # Increment sequence number
                sent_bytes += len(chunk)
                break

        time.sleep(0.01)  # Short sleep to avoid busy waiting

        # Retransmission logic
        with lock:
            # Retransmit packets if the send window is full
            if len(send_window) >= win:
                print(f"Retransmitting packet seq_num: {send_window[0][0]}")  # Debug print
                # Retransmit the first packet in the send window
                s.sendto(send_window[0][1], (host, port))  # Resend the first packet
                retransmissions += 1  # Increment the retransmission counter

# Wait for the reader thread to finish
reader_thread.join()

# Send an empty packet with just the sequence number to signal the end
s.sendto(seq_num.to_bytes(2, 'big'), (host, port))

# Print statistics
print(f'Sent: {sent_bytes} bytes, Pack size: {pack_sz + 2}, Total chunks: {len(input_data_chunks)}, Retransmissions: {retransmissions}')
s.close()
