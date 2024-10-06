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

if len(sys.argv) != 3:
    print('Use: '+sys.argv[0]+' pack_sz win host port')
    sys.exit(1)
    
pack_sz = int(sys.argv[1])
win = int(sys.argv[2])
host = sys.argv[3]
port = sys.argv[4]

s = jsockets.socket_tcp_connect(host, port)

if s is None:
    print('could not open socket')
    sys.exit(1)

# Creo thread que lee desde el socket hacia stdout:
newthread = threading.Thread(target=Rdr, args=(s,))
newthread.start()

# En este otro thread leo desde stdin hacia socket:
for line in sys.stdin:
    s.send(line)

# time.sleep(3)  # dar tiempo para que vuelva la respuesta
s.close()
