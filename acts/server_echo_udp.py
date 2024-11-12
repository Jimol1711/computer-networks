#!/usr/bin/python3
# Echo server UDP program

import jsockets
import sys
import socket

# Replace this with your actual Wi-Fi IP address, e.g., '192.168.1.10'
wifi_ip = '10.0.2.15'

s = jsockets.socket_bind(socket.SOCK_DGRAM, 1818, wifi_ip)
if s is None:
    print('could not open socket')
    sys.exit(1)
print('Server is running on IP', wifi_ip, 'and port 1818')

while True:
    data, addr = s.recvfrom(1024)
    if not data:
        break
    s.sendto(data, addr)

s.close()
