# Múltiples archivos grandes en paralelo
echo "Three large files in parallel for echo2 port 1818 size 1000:"
for i in 1 2 3; do
  time ../client_bw.py 1000 localhost 1818 < largefile${i}.bin > OUT3_${i}_1000 &
done
wait
echo "Three large files in parallel for echo2 port 1818 size 2000:"
for i in 1 2 3; do
  time ../client_bw.py 2000 localhost 1818 < largefile${i}.bin > OUT3_${i}_2000 &
done
wait
echo "Three large files in parallel for echo2 port 1818 size 5000:"
for i in 1 2 3; do
  time ../client_bw.py 5000 localhost 1818 < largefile${i}.bin > OUT3_${i}_5000 &
done
wait
echo "Three large files in parallel for echo2 port 1818 size 8000:"
for i in 1 2 3; do
  time ../client_bw.py 8000 localhost 1818 < largefile${i}.bin > OUT3_${i}_8000 &
done
wait