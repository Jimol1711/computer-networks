#!/usr/bin/python3
# Echo client UDP program
import jsockets
import sys

if len(sys.argv) < 2:
    print("Usage: ./client_echo_udp.py <message>")
    sys.exit(1)

server_address = 'anakena.dcc.uchile.cl'
server_port = 1818
message = sys.argv[1]

# Create a UDP socket and connect to the server
s = jsockets.socket_udp_connect(server_address, server_port)
if s is None:
    print(f"Could not connect to server at {server_address}:{server_port}")
    sys.exit(1)

# Send the message to the server
s.send(message.encode())

# Receive the echoed response
data, _ = s.recvfrom(1024*1024)  # Buffer size matches the server
print(f"Received: {data.decode()}")

s.close()
