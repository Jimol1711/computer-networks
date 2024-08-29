#!/usr/bin/python3
# Echo client program
# Version con dos threads: uno lee de stdin hacia el socket y el otro al revés
import jsockets
import sys, threading
import time

def Rdr(s):
    while True:
        try:
            data=s.recv(1500)
        except:
            data = None
        if not data: 
            break
        print(data, end = '')

if len(sys.argv) != 4:
    print('Use: '+sys.argv[0]+'size host port')
    sys.exit(1)

size = sys.argv[1]
host = sys.argv[2]
port = sys.argv[3]

s = jsockets.socket_tcp_connect(host, port)

if s is None:
    print('could not open socket')
    sys.exit(1)

# Creo thread que lee desde el socket hacia stdout:
newthread = threading.Thread(target=Rdr, args=(s,))
newthread.start()

# En este otro thread leo desde stdin hacia socket:
for byte in sys.stdin:
    s.send(byte)

time.sleep(3)  # dar tiempo para que vuelva la respuesta
s.close()
