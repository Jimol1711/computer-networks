#!/bin/bash

# Experimento en localhost para un archivo grande en server_echo4.py puerto 1819

# Single large file
echo "Single large file experiment for echo4 port 1819"
time ../client_bw.py 1000 localhost 1819 < largefile.bin > OUT4_LARGE_1000
time ../client_bw.py 2000 localhost 1819 < largefile.bin > OUT4_LARGE_2000
time ../client_bw.py 5000 localhost 1819 < largefile.bin > OUT4_LARGE_5000
time ../client_bw.py 8000 localhost 1819 < largefile.bin > OUT4_LARGE_8000