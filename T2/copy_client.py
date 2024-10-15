#!/usr/bin/python3
# Echo client program
# Version con dos threads: uno lee de stdin hacia el socket y el otro al revés
import jsockets
import sys, threading, time, struct

# Shared memory variables
lock = threading.Lock()  # Mutex for shared memory access
send_window = []  # Sequence numbers of sent but not yet received packets
recv_window = []  # To store received sequence numbers (for simulation purposes)
seq_num = 0  # Sequence number of the next packet to send
last_acked = -1  # Last sequence number that was successfully received back
timed_out = False  # Flag for handling timeout and retransmission
finished_sending = False  # Flag for signaling when sending is complete

# function to redefine timeout
def adaptative_timeout(rtt):
    return rtt * 3

def Rdr(s, num_bytes):
    global last_acked, timed_out
    received_bytes = 0
    start_time = time.time()
    rtt = 0.5  # Initial RTT estimate for timeout

    while received_bytes < num_bytes:
        try:
            # Receive data from the server
            data, addr = s.recvfrom(pack_sz + 2)
            if not data:
                break
            # Extract the sequence number from the first 2 bytes
            seq_num_received = struct.unpack('>H', data[:2])[0]
            packet_data = data[2:]  # Extract actual data without sequence number

            with lock:
                if seq_num_received == (last_acked + 1) % 65536:
                    sys.stdout.buffer.write(packet_data)
                    received_bytes += len(packet_data)
                    last_acked = seq_num_received  # Update the last acknowledged packet
                    recv_window.append(last_acked)  # Store received sequence number for tracking

            # Update RTT and adaptive timeout
            end_time = time.time()
            rtt = adaptative_timeout(end_time - start_time)
            start_time = end_time

            # Reset timed_out flag if data is successfully received
            timed_out = False

        except Exception as e:
            print("Error receiving data:", str(e))
            break

if len(sys.argv) != 5:
    print('Use: '+sys.argv[0]+' pack_sz win host port')
    sys.exit(1)

pack_sz = int(sys.argv[1]) - 2  # Subtract 2 bytes for sequence number
win = int(sys.argv[2]) # Window size
host = sys.argv[3] # host server
port = int(sys.argv[4]) # port to read/write from/to

s = jsockets.socket_udp_connect(host, port)

if s is None:
    print('could not open socket')
    sys.exit(1)

total_bytes = len(sys.stdin.buffer.read())
input_data = sys.stdin.buffer.read(pack_sz)

# Creo thread que lee desde el socket hacia stdout:
reader_thread = threading.Thread(target=Rdr, args=(s, pack_sz))
reader_thread.start()

# Sending thread - adding sequence number
sent_bytes = 0
rtt = 0.5  # Initial RTT
timeout_duration = rtt * 3
start_time = time.time()  # Initial start time

while sent_bytes < total_bytes:
    with lock:
        if len(send_window) < win:  # Only send if window isn't full
            chunk = input_data[sent_bytes:sent_bytes+pack_sz]
            # Add sequence number (2 bytes) to the chunk
            data_with_seq = struct.pack('>H', seq_num) + chunk
            print(host, port)
            s.sendto(data_with_seq, (host, port))
            send_window.append(seq_num)  # Add to send window

            sent_bytes += len(chunk)
            seq_num = (seq_num + 1) % 65536  # Increment sequence number

            # Implement adaptive timeout for retransmissions
            start_time = time.time()
    # Check if timeout occurred for retransmission
    if time.time() - start_time >= timeout_duration:
        timed_out = True
        with lock:
            if send_window:  # If there are unacknowledged packets in the window
                # Retransmit the first unacknowledged packet in the window
                data_with_seq = struct.pack('>H', send_window[0]) + input_data[send_window[0]*pack_sz:(send_window[0]+1)*pack_sz]
                s.sendto(data_with_seq, (host, port))
                print(f"Retransmitting packet {send_window[0]}")
        # Reset start_time after retransmission
        start_time = time.time()

    # Check if the first packet in the window has been acknowledged
    with lock:
        if send_window and send_window[0] <= last_acked:
            send_window.pop(0)  # Remove the acknowledged packet from the window
            timed_out = False  # Reset timeout flag as packet is acknowledged

reader_thread.join()

# Send an empty packet with just the sequence number to signal the end
s.sendto(struct.pack('>H', seq_num), (host, port))

# Print statistics
print(f'Used: pack: {pack_sz + 2}, maxwin: {win}')
print(f'Send errors: {len(send_window)}')
print(f'Receive errors: {len(recv_window)}')

time.sleep(3) # dar tiempo para que vuelva la respuesta
s.close()
