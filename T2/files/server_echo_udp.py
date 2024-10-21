#!/usr/bin/python3
# Echo server UDP program - version of server_echo_udp.c, mono-cliente
import Redes.T2.files.jsockets as jsockets
import sys # Se importó el módulo sys que no estaba importado

s = jsockets.socket_udp_bind(1818)
if s is None:
    print('could not open socket')
    sys.exit(1)
print('Server is running on port 1818')

while True:
    # Se modificó el servidor para que reciba 1024 * 1024 bytes
    data, addr = s.recvfrom(1024*1024)
    if not data: break
    s.sendto(data, addr)

s.close()
