# Múltiples archivos medianos en paralelo
echo "Twenty medium files in parallel for echo5 port 1820 size 1000:"
for i in $(seq 1 20); do
  time ../client_bw.py 1000 localhost 1820 < ./medium_files/file${i}.bin > ./trash/OUT20_${i}_1000 &
done
wait
echo "Twenty medium files in parallel for echo5 port 1820 size 2000:"
for i in $(seq 1 20); do
  time ../client_bw.py 2000 localhost 1820 < ./medium_files/file${i}.bin > ./trash/OUT20_${i}_2000 &
done
wait
echo "Twenty medium files in parallel for echo5 port 1820 size 5000:"
for i in $(seq 1 20); do
  time ../client_bw.py 5000 localhost 1820 < ./medium_files/file${i}.bin > ./trash/OUT20_${i}_5000 &
done
wait
echo "Twenty medium files in parallel for echo5 port 1820 size 8000:"
for i in $(seq 1 20); do
  time ../client_bw.py 8000 localhost 1820 < ./medium_files/file${i}.bin > ./trash/OUT20_${i}_8000 &
done
wait