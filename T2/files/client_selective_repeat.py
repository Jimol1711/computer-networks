#!/usr/bin/python3
import jsockets
import sys
import threading
import time

# error handling for arguments
if len(sys.argv) != 5:
    print('Use: ' + sys.argv[0] + ' pack_sz win host port', file=sys.stderr)
    sys.exit(1)

# input variables
pack_sz = int(sys.argv[1]) - 2
win = int(sys.argv[2])
host = sys.argv[3]
port = int(sys.argv[4])

# timeout
timeout = 0.5

# Seq num variables
seq_base = 0
next_seq_number = 0

# counters
num_retransmissions = 0
num_out_of_order = 0

# mutex and condition
mutex = threading.Lock()
cond = threading.Condition(mutex)

# window variables
acked = [False] * win # Lista para mantener el estado de los ACKs de los paquetes
send_times = [0] * win  # Tiempos de envío de los paquetes
received_chunks = [None] * win  # Almacena los paquetes recibidos fuera de orden en el receptor

# receiver function
def Rdr(s, total_bytes, size):
    global seq_base
    recibido = 0
    
    # Recibir los datos mientras no se haya recibido el total de bytes
    while recibido < total_bytes or total_bytes == 0: 
        try:
            data = s.recv(size + 2)
        except Exception:
            data = None
        if not data:
            break
        
        # Obtener el número de secuencia del paquete
        seq_number_received = int.from_bytes(data[:2], 'big')
        chunk = data[2:]
        
        with mutex:
            if seq_base <= seq_number_received < seq_base + win:
                # Almacenar el paquete recibido en su posición
                received_chunks[seq_number_received % win] = chunk
                acked[seq_number_received % win] = True  # Marcar el paquete como confirmado

                # Enviar el ACK de vuelta al emisor
                ack_packet = seq_number_received.to_bytes(2, 'big')
                s.send(ack_packet)

                # Si es el paquete esperado, escribir en la salida y mover la seq_base
                while seq_base < next_seq_number and acked[seq_base % win]:
                    sys.stdout.buffer.write(received_chunks[seq_base % win])
                    acked[seq_base % win] = False
                    received_chunks[seq_base % win] = None
                    seq_base += 1
                cond.notify_all()

# connection
s = jsockets.socket_udp_connect(host, port)
if s is None:
    print('Could not open socket')
    sys.exit(1)

# sending
total_sent = 0
data_chunks = []
while True:
    data = sys.stdin.buffer.read(pack_sz - 2)
    if not data:
        break
    data_chunks.append(data)
    total_sent += len(data)

# Crear un thread para recibir los datos desde el servidor (hilo receptor)
newthread = threading.Thread(target=Rdr, args=(s, total_sent, pack_sz))
newthread.start()

for chunk in data_chunks:
    with mutex:
        # Verificar si la ventana está llena, si está llena esperar
        while next_seq_number >= seq_base + win:
            cond.wait()

        # Preparar el paquete con número de secuencia
        packet = next_seq_number.to_bytes(2, 'big') + chunk

        # Enviar el paquete
        s.send(packet)
        acked[next_seq_number % win] = False
        send_times[next_seq_number % win] = time.time() 

        # Avanzar el número de secuencia
        next_seq_number += 1

    # Verificar si algún paquete necesita retransmisión por timeout
    with mutex:
        for i in range(seq_base, next_seq_number):
            if not acked[i % win] and (time.time() - send_times[i % win]) > timeout:
                # Retransmitir solo el paquete no confirmado
                num_retransmissions += 1
                packet = i.to_bytes(2, 'big') + data_chunks[i]
                s.send(packet)
                send_times[i % win] = time.time()

# Esperar a que todos los ACKs hayan sido recibidos
with mutex:
    while seq_base < next_seq_number:
        cond.wait()

# Enviar paquete vacío para indicar fin de transmisión
s.send(next_seq_number.to_bytes(2, 'big'))

# Final stats and closing
print('Using: pack_sz:', pack_sz + 2, 'maxwin:', win, file=sys.stderr)
print('Send errors:', num_retransmissions, file=sys.stderr)
print('Receive errors:', num_out_of_order, file=sys.stderr)

# Cerrar el socket
s.close()