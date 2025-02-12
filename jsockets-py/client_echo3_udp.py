#!/usr/bin/python3
# Echo client program
# Version con dos threads: uno lee de stdin hacia el socket y el otro al revés
import jsockets
import sys, threading
import time

def Rdr(s):
    while True:
        try:
            data=s.recv(1500).decode()
        except:
            data = None
        if not data: 
            break
        print(data, end = '')

if len(sys.argv) != 3:
    print('Use: '+sys.argv[0]+' host port')
    sys.exit(1)

s = jsockets.socket_udp_connect(sys.argv[1], sys.argv[2])
if s is None:
    print('could not open socket')
    sys.exit(1)
# print(f'Client sending on port 1818')

# Esto es para dejar tiempo al server para conectar el socket
s.send(b'hola')
s.recv(1024)

# Creo thread que lee desde el socket hacia stdout:
newthread = threading.Thread(target=Rdr, args=(s,))
newthread.start()

# En este otro thread leo desde stdin hacia socket:
for line in sys.stdin:
    try:
        s.send(line.encode())
    except Exception as e:
        print(f"Error sending data: {e}", file=sys.stderr)
        continue

time.sleep(3)  # dar tiempo para que vuelva la respuesta
s.close()
