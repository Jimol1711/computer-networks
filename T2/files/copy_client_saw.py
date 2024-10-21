#!/usr/bin/python3
# Echo client program
# Stop and Wait sin pérdidas
# Version con dos threads: uno lee de stdin hacia el socket y el otro al revés
import Redes.T2.files.jsockets as jsockets
import sys, threading
import time

# Mutex and condition
mutex = threading.Lock()
condition = threading.Condition(mutex)
data_received = False
# timeout = 0.5
# RTT = 0
# retransmissions = 0

def Rdr(s):
    global data_received
    while True:
        data = s.recv(pack_sz + 2)

        # extract sequence number and data
        # seq_num_received = int.from_bytes(data[:2], 'big')
        # packet_data = data[2:]

        if not data:
            print("Finished receiving data")
            break

        sys.stdout.buffer.write(data)

        # flush is necessary
        sys.stdout.buffer.flush()
    
        # Notify receiving of the data
        with condition:
            data_received = True
            condition.notify()

if len(sys.argv) != 5:
    print('Use: '+sys.argv[0]+' pack_sz win host port')
    sys.exit(1)

pack_sz = int(sys.argv[1]) - 2
win = int(sys.argv[2]) # Not used
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
        # start_time = time.time()
        s.sendto(chunk, (host, port))
        data_received = False

        # Wait for acknowledgment
        while not data_received:
            condition.wait() # aquí iría timeout, pero dado que no hay perdidas no lo pongo

        # rtt = time.time() - start_time
        # RTT = rtt
        # timeout = RTT * 3

reader_thread.join()

time.sleep(3)  # dar tiempo para que vuelva la respuesta

# print statistics
print('Usando: pack:', pack_sz, 'maxwin:', win)
print('Errores envío:', 0)
print('Errores recepción:', 0)
s.close()
