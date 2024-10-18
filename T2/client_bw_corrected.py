#!/usr/bin/python3
# Echo client program
# Version con dos threads: uno lee de stdin hacia el socket y el otro al revés
import jsockets
import sys, threading
import time

# Mutex and condition
mutex = threading.Lock()
condition = threading.Condition(mutex)
data_received = False

# global variables for Go Back N
req_num = 0
seq_num = 0
seq_base = 0
seq_max = 0

def Rdr(s, win_size):
    global data_received, req_num, seq_base
    while True:
        data = s.recv(pack_sz + 2)

        # extract sequence number and data
        seq_num_received = int.from_bytes(data[:2], 'big')
        packet_data = data[2:]

        if not data:
            print("Finished receiving data")
            break

        with mutex:
            if seq_num_received == req_num:
                sys.stdout.buffer.write(packet_data)
                sys.stdout.buffer.flush()

                req_num += 1

                data_received = True
                condition.notify()

            else:
                continue

if len(sys.argv) != 5:
    print('Use: '+sys.argv[0]+' pack_sz win host port')
    sys.exit(1)

pack_sz = int(sys.argv[1]) - 2
win = int(sys.argv[2])
host = sys.argv[3]
port = int(sys.argv[4])

s = jsockets.socket_udp_connect(host, port)

if s is None:
    print('could not open socket')
    sys.exit(1)

# Creo thread que lee desde el socket hacia stdout:
reader_thread = threading.Thread(target=Rdr, args=(s,))
reader_thread.start()

# En este otro thread leo desde stdin hacia socket por bloques:
while True:

    chunk = sys.stdin.buffer.read(pack_sz)
    if chunk == b'':
        break

    # Send and wait for acknowledgment
    with condition:
        s.sendto(chunk, (host, port))
        data_received = False
        while not data_received:
            condition.wait()

reader_thread.join()

time.sleep(3)  # dar tiempo para que vuelva la respuesta

# print statistics
print('Usando: pack:', pack_sz, 'maxwin:', win)
print('Errores envío:', 0)
print('Errores recepción:', 0)
s.close()
