#!/bin/bash

# Múltiples archivos pequeños en paralelo
echo "One hundred small files in parallel for anakena echo4 port 1819 size 1000:" | tee ./times/real_time1.txt
for i in $(seq 1 100); do
  time ../client_bw.py 1000 anakena.dcc.uchile.cl 1819 < ./small_files/file${i}.bin > ./trash/OUT100_${i}_1000 &
  { time ../client_bw.py 1000 anakena.dcc.uchile.cl 1819 < ./small_files/file${i}.bin > ./trash/OUT100_${i}_1000 ; } 2>> ./times/real_time1.txt &
done
wait
echo "One hundred small files in parallel for anakena echo4 port 1819 size 2000:" | tee ./times/real_time2.txt
for i in $(seq 1 100); do
  time ../client_bw.py 2000 anakena.dcc.uchile.cl 1819 < ./small_files/file${i}.bin > ./trash/OUT100_${i}_2000 &
  { time ../client_bw.py 2000 anakena.dcc.uchile.cl 1819 < ./small_files/file${i}.bin > ./trash/OUT100_${i}_2000 ; } 2>> ./times/real_time2.txt &
done
wait
echo "One hundred small files in parallel for anakena echo4 port 1819 size 5000:" | tee ./times/real_time5.txt
for i in $(seq 1 100); do
  time ../client_bw.py 5000 anakena.dcc.uchile.cl 1819 < ./small_files/file${i}.bin > ./trash/OUT100_${i}_5000 &
  { time ../client_bw.py 5000 anakena.dcc.uchile.cl 1819 < ./small_files/file${i}.bin > ./trash/OUT100_${i}_5000 ; } 2>> ./times/real_time5.txt &
done
wait
echo "One hundred small files in parallel for anakena echo4 port 1819 size 8000:" | tee ./times/real_time8.txt
for i in $(seq 1 100); do
  time ../client_bw.py 8000 anakena.dcc.uchile.cl 1819 < ./small_files/file${i}.bin > ./trash/OUT100_${i}_8000 &
  { time ../client_bw.py 8000 anakena.dcc.uchile.cl 1819 < ./small_files/file${i}.bin > ./trash/OUT100_${i}_8000 ; } 2>> ./times/real_time8.txt &
done
wait