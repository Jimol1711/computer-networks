#!/usr/bin/python3
# Echo client program
# Version con dos threads: uno lee de stdin hacia el socket y el otro al revés
import jsockets
import sys, threading
import time

def Rdr(s, total_bytes):
    received_bytes = 0
    while received_bytes < total_bytes:

        data=s.recv(read_write_size)

        if not data: 
            break

        sys.stdout.buffer.write(data)
        received_bytes += len(data)
    sys.stdout.buffer.flush()

if len(sys.argv) != 4:
    print('Use: '+sys.argv[0]+' size host port')
    sys.exit(1)

read_write_size = int(sys.argv[1])
host = sys.argv[2]
port = sys.argv[3]

s = jsockets.socket_tcp_connect(host, port)

if s is None:
    print('could not open socket')
    sys.exit(1)

input_data = sys.stdin.buffer.read()
total_bytes = len(input_data)

# Creo thread que lee desde el socket hacia stdout:
reader_thread = threading.Thread(target=Rdr, args=(s, total_bytes))
reader_thread.start()

# En este otro thread leo desde stdin hacia socket:
sent_bytes = 0
for i in range(0, total_bytes, read_write_size):
    chunk = input_data[i:i+read_write_size]
    s.send(chunk)
    sent_bytes += len(chunk)

reader_thread.join()

time.sleep(3)  # dar tiempo para que vuelva la respuesta
s.close()
