#!/bin/bash

# Experimento en localhost para un archivo grande en server_echo5.py puerto 1820

# Single large file
echo "Single large file experiment for echo5 port 1820:"
time ../client_bw.py 1000 localhost 1820 < ./big_files/file1.bin > ./trash/OUT2_LARGE_8000
time ../client_bw.py 2000 localhost 1820 < ./big_files/file1.bin > ./trash/OUT2_LARGE_8000
time ../client_bw.py 5000 localhost 1820 < ./big_files/file1.bin > ./trash/OUT2_LARGE_8000
time ../client_bw.py 8000 localhost 1820 < ./big_files/file1.bin > ./trash/OUT2_LARGE_8000