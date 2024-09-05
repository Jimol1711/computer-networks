#!/bin/bash

# Experimento en localhost para un archivo grande en server_echo2.py puerto 1818

# Single large file
echo "Single large file experiment for echo2 port 1818:"
time ../client_bw.py 1000 localhost 1818 < ./big_files/file1.bin > ./trash/OUT2_LARGE_1000
time ../client_bw.py 2000 localhost 1818 < ./big_files/file1.bin > ./trash/OUT2_LARGE_2000
time ../client_bw.py 5000 localhost 1818 < ./big_files/file1.bin > ./trash/OUT2_LARGE_5000
time ../client_bw.py 8000 localhost 1818 < ./big_files/file1.bin > ./trash/OUT2_LARGE_8000