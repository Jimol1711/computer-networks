#!/usr/bin/python3
# Echo client program
# Version with two threads: one reads from stdin to the socket and the other does the reverse
import jsockets
import sys, threading
import time

# error handling
if len(sys.argv) != 5:
    print('Use: ' + sys.argv[0] + ' pack_sz win host port', file=sys.stderr)
    sys.exit(1)

# mutex
mutex = threading.Lock()
cond = threading.Condition()

# input variables
pack_sz = int(sys.argv[1]) - 2
win = int(sys.argv[2])
host = sys.argv[3]
port = int(sys.argv[4])

# go back n variables
req_num = 0
seq_base = 0
seq_max = 0
seq_num = 0

# timeout and unacked dict
timeout = 0.5
unacked_packets = {}

# retransmissions and final packet flags
num_retransmissions = 0 # Esta variable no se está modificando
num_out_of_order = 0
final_packet_sent = False
final_packet_acked = False
terminate_program = False

# Receiver function
def Rdr(s):
    global req_num, final_packet_acked, terminate_program
    while True:
        data = s.recv(pack_sz + 2)
        
        if not data:
            print("No more data, exiting receiver", file=sys.stderr)
            break

        # seq num and data
        seq_num_received = int.from_bytes(data[:2], 'big')
        packet_data = data[2:]

        # veo si es el sequence number que espera y si no, lo ignora
        # si es el paquete vacío notifica para que el programa se cierre
        # aquí está el problema 1, no sé porqué no se está cerrando
        with cond:
            if seq_num_received == req_num:
                if packet_data == b'':  # Empty packet indicates end

                    # Esto nunca se imprime, pero sería lo correcto
                    print(f"Final packet received (Seq: {seq_num_received}). Exiting.", file=sys.stderr)
                    print('Using: pack:', pack_sz, 'maxwin:', win, file=sys.stderr)
                    print('Send errors:', num_retransmissions, file=sys.stderr)
                    print('Receive errors:', 0, file=sys.stderr) # esto está en 0 porque aún estoy viendo como detectar los errores de recibo

                    # aquí cambio las flags pero tampoco me funciona para cerrar el programa
                    final_packet_acked = True
                    terminate_program = True
                    cond.notify_all()
                    break

                sys.stdout.buffer.write(packet_data)
                # sys.stdout.buffer.flush()
                req_num += 1
            else:
                continue

s = jsockets.socket_udp_connect(host, port)
if s is None:
    print('Could not open socket')
    sys.exit(1)

reader_thread = threading.Thread(target=Rdr, args=(s,))
reader_thread.start()

with mutex:
    seq_base = 0
    seq_max = seq_base + win - 1

# Function to resend unacknowledged packets
def resend_unacked_packets():
    global seq_base, num_retransmissions
    with mutex:
        num_retransmissions += 1
        print("Timeout! Resending unacknowledged packets from", seq_base, file=sys.stderr)
        for sn in range(seq_base, seq_num):
            if sn in unacked_packets:
                s.sendto(unacked_packets[sn], (host, port))
                print(f"Retransmitting packet {sn}", file=sys.stderr)

while True:
    with cond:
        if terminate_program:
            break

        if seq_num <= seq_max:
            chunk = sys.stdin.buffer.read(pack_sz)
            if chunk == b'': # EOF
                final_packet_sent = True
                seq_num_bytes = seq_num.to_bytes(2, 'big')
                packet = seq_num_bytes
                s.sendto(packet, (host, port))

                unacked_packets[seq_num] = packet
                print(f"Sent final empty packet {seq_num}")
                seq_num += 1
                break

            seq_num_bytes = seq_num.to_bytes(2, 'big')
            packet = seq_num_bytes + chunk

            s.sendto(packet, (host, port))
            unacked_packets[seq_num] = packet
            print(f"Sent packet {seq_num}", file=sys.stderr)
            seq_num += 1

    start_time = time.time()

    with cond:
        while req_num <= seq_base and not terminate_program:
            elapsed_time = time.time() - start_time
            if elapsed_time >= timeout:
                resend_unacked_packets()
                start_time = time.time()
            cond.wait(timeout - elapsed_time)

    with mutex:
        seq_base = req_num
        seq_max = seq_base + win - 1

with cond:
    while not final_packet_acked and not terminate_program:
        elapsed_time = time.time() - start_time
        if elapsed_time >= timeout:
            resend_unacked_packets()
            start_time = time.time()
        cond.wait(timeout - elapsed_time)

reader_thread.join()

# Esto nunca se imprime
print('Using: pack:', pack_sz + 2, 'maxwin:', win, file=sys.stderr)
print('Send errors:', num_retransmissions, file=sys.stderr)
print('Receive errors:', num_out_of_order, file=sys.stderr)

# closing connection
s.close()
