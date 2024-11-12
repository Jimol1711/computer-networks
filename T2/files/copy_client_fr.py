#!/usr/bin/python3
import sys
import jsockets
import threading
import time

PACK_SZ = int(sys.argv[1])
N = int(sys.argv[2])
SERVER_HOSTNAME = sys.argv[3]
SERVER_PORT = int(sys.argv[4])

client_socket = jsockets.socket_udp_connect(SERVER_HOSTNAME, SERVER_PORT)
if client_socket is None:
    print("could not open socket", file=sys.stderr)
    sys.exit(1)

mutex = threading.Lock()
window_full = threading.Condition(mutex)
seq_base = 0
seq_no = 0
ack_received = [-1] * N
pending_ack = [False] * N
rtt_start = {} 
retransmitted = set()  
window_size = N

errores_envio = 0
errores_recepcion = 0

input_data = sys.stdin.buffer.read()
packets = [input_data[i:i + PACK_SZ - 2] for i in range(0, len(input_data), PACK_SZ - 2)]
max_seq_no = len(packets)

rtt = 0.5
timeout = 0.5


received_packets = [None] * max_seq_no

def send_packet():
    global seq_no, seq_base, errores_envio
    while seq_base < max_seq_no:
        with mutex:
            while seq_no < seq_base + window_size and seq_no < max_seq_no:
                packet = seq_no.to_bytes(2, 'big') + packets[seq_no]
                try:
                    client_socket.send(packet)
                    if seq_no not in retransmitted:  # guardamos el tiempo si no es una retransmisión
                        rtt_start[seq_no] = time.time()
                    pending_ack[seq_no % N] = True
                except Exception as e:
                    errores_envio += 1
                seq_no += 1

        for i in range(seq_base, seq_no):
            if pending_ack[i % N]:
                client_socket.send(i.to_bytes(2, 'big') + packets[i])
                retransmitted.add(i)  # paquete como retransmitido
                errores_envio += 1

        time.sleep(timeout)

def receive_ack():
    global seq_base, ack_received, errores_recepcion, timeout, rtt, rtt_start
    while seq_base < max_seq_no:
        try:
            data = client_socket.recv(PACK_SZ)
            ack_seq_no = int.from_bytes(data[:2], byteorder='big')
            packet_data = data[2:]  

            with mutex:
                if seq_base <= ack_seq_no < seq_base + window_size:
                    ack_received[ack_seq_no % N] = ack_seq_no
                    pending_ack[ack_seq_no % N] = False
                    received_packets[ack_seq_no] = packet_data  

                    if ack_seq_no in rtt_start and ack_seq_no not in retransmitted:
                        rtt = time.time() - rtt_start[ack_seq_no]
                        timeout = rtt * 3

                    while seq_base < max_seq_no and ack_received[seq_base % N] != -1:
                        seq_base += 1
                        ack_received[seq_base % N] = -1
                else:
                    errores_recepcion += 1
        except TimeoutError:
            print("timeout", file=sys.stderr)


ack_thread = threading.Thread(target=receive_ack)
ack_thread.start()

send_packet()
client_socket.send(seq_no.to_bytes(2, byteorder='big'))

ack_thread.join()


with open("OUT", "wb") as f:
    for packet in received_packets:
        if packet is not None:
            f.write(packet)

print(f"Usando: pack: {PACK_SZ}, maxwin: {N}", file=sys.stderr)
print(f"Errores envío: {errores_envio}", file=sys.stderr)
print(f"Errores recepción: {errores_recepcion}", file=sys.stderr)

client_socket.close()