#!/usr/bin/python3
# Echo client program que mide ancho de banda
# Version con dos threads: uno lee de stdin hacia el socket y el otro al revés
# Stop and Wait, se envía y se bloquea hasta recibir confirmación de envío del paquete.

import jsockets
import sys, threading
import time
import queue

PACK_SZ=int(sys.argv[1])
win=int(sys.argv[2])
eof=0

# Global variables
mutex = threading.Lock()  # mutex for shared resources
cond = threading.Condition()  # condition variable
buffer = queue.Queue()  # shared buffer to hold data
sent = [False] * win  # keeps track of which packets are sent
base = 0  # base of the window
next_seq_num = 0  # next sequence number to send
window = []  # stores packets in the window
timeout = 0.5  # timeout for the condition variable

# counter variables
num_retransmissions = 0
num_out_of_order = 0

def Rdr(s):
    global eof, base
    sz = 0
    while eof == 0 or sz != eof:
        try:
            data=s.recv(PACK_SZ)
        except:
            data = None
        if not data:
            break
        sys.stdout.buffer.write(data)
        sz += len(data)

        with cond:
            buffer.put(data)
            base += 1
            cond.notify_all()

if len(sys.argv) != 5:
    print('Use: '+sys.argv[0]+'pack_sz win host port', file=sys.stderr)
    sys.exit(1)

s = jsockets.socket_udp_connect(sys.argv[3], sys.argv[4])
if s is None:
    print('could not open socket', file=sys.stderr)
    sys.exit(1)

# Creo thread que lee desde el socket hacia stdout:
newthread = threading.Thread(target=Rdr, args=(s,))
newthread.start()

# En este otro thread leo desde stdin hacia socket:
sz = 0
eof = 0
while True:
    with cond:

        while next_seq_num >= base + win:
            cond.wait(timeout)

        data = sys.stdin.buffer.read(PACK_SZ)
        if not data:
            break
        s.send(data)
        window.append(data)
        sent[next_seq_num % win] = True
        sz += len(data)
        next_seq_num += 1

eof = sz
newthread.join()

# print statistics
print('Usando: pack:', PACK_SZ, 'maxwin:', win, file=sys.stderr)
print('Errores envío:', num_retransmissions, file=sys.stderr)
print('Errores recepción:', num_out_of_order, file=sys.stderr)

s.close()