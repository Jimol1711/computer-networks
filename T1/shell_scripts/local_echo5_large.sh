#!/bin/bash

# Experimento en localhost para un archivo grande en server_echo5.py puerto 1820

# Single large file
echo "Single large file experiment for echo5 port 1820:"
time ../client_bw.py 1000 localhost 1820 < largefile.bin > OUT5_LARGE_1000
time ../client_bw.py 2000 localhost 1820 < largefile.bin > OUT5_LARGE_2000
time ../client_bw.py 5000 localhost 1820 < largefile.bin > OUT5_LARGE_5000
time ../client_bw.py 8000 localhost 1820 < largefile.bin > OUT5_LARGE_8000