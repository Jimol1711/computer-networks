#!/usr/bin/python3
# Echo client program
# Version con dos threads: uno lee de stdin hacia el socket y el otro al revés
import jsockets
import sys, threading
import time

def Rdr(s):
    while True:
        data = s.recv(read_write_size)

        if not data: 
            break

        sys.stdout.buffer.write(data)
        # sys.stdout.buffer.flush()

if len(sys.argv) != 4:
    print('Use: '+sys.argv[0]+' size host port')
    sys.exit(1)

read_write_size = int(sys.argv[1])
host = sys.argv[2]
port = int(sys.argv[3])

s = jsockets.socket_udp_connect(host, port)

if s is None:
    print('could not open socket')
    sys.exit(1)

# Creo thread que lee desde el socket hacia stdout:
reader_thread = threading.Thread(target=Rdr, args=(s,))
reader_thread.start()

# En este otro thread leo desde stdin hacia socket por bloques:
while True:
    # Leer read_write_size bytes desde stdin
    chunk = sys.stdin.buffer.read(read_write_size)
    if not chunk:
        break  # Si ya no hay más datos, salir del bucle

    # Enviar el chunk leído al socket
    s.send(chunk)

reader_thread.join()

time.sleep(3)  # dar tiempo para que vuelva la respuesta
s.close()
