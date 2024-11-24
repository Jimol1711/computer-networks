#!/usr/bin/python3
from scapy.all import ARP, sr1
import sys

arp_req = ARP(pdst="10.0.2.15")
arp_res = sr1(arp_req, timeout=2, verbose=0)
print(arp_res, file=sys.stderr)
if arp_res:
    print("MAC Address:", arp_res.hwsrc)
else:
    print("No ARP response received")
