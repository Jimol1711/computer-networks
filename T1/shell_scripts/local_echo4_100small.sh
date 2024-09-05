#!/bin/bash

# Múltiples archivos pequeños en paralelo
echo "One hundred small files in parallel for echo4 port 1819 size 1000:"
for i in $(seq 1 100); do
  time ../client_bw.py 1000 localhost 1819 < ./small_files/file${i}.bin > ./trash/OUT100_${i}_1000 &
done
wait
echo "One hundred small files in parallel for echo4 port 1819 size 2000:"
for i in $(seq 1 100); do
  time ../client_bw.py 2000 localhost 1819 < ./small_files/file${i}.bin > ./trash/OUT100_${i}_2000 &
done
wait
echo "One hundred small files in parallel echo4 port 1819 size 5000:"
for i in $(seq 1 100); do
  time ../client_bw.py 5000 localhost 1819 < ./small_files/file${i}.bin > ./trash/OUT100_${i}_5000 &
done
wait
echo "One hundred small files in parallel echo4 port 1819 size 8000:"
for i in $(seq 1 100); do
  time ../client_bw.py 8000 localhost 1819 < ./small_files/file${i}.bin > ./trash/OUT100_${i}_8000 &
done
wait