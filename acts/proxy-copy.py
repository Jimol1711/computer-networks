#!/usr/bin/python3
import sys
import os
import jsockets
import threading

def copy_and_log(conn1, conn2, logfile, direction):
    while True:
        try:
            data = conn1.recv(1500)
        except:
            data = None

        if not data:
            break

        if direction == "to_server":
            header = b"\n\n>>> to server\n"
        else:
            header = b"\n\n<<< from server\n"

        with open(logfile, 'ab') as f:
            f.write(header + data)

        conn2.send(data)

    conn2.close()

def proxy(conn, host, portout, logfile):

    conn2 = jsockets.socket_tcp_connect(host, portout)

    if conn2 is None:
        print('conexión rechazada por ' + host + ', ' + portout)
        sys.exit(1)

    print('Cliente conectado')

    # Creación de dos hilos: uno para cada dirección de la comunicación
    thread1 = threading.Thread(target=copy_and_log, args=(conn, conn2, logfile, "to_server"))
    thread2 = threading.Thread(target=copy_and_log, args=(conn2, conn, logfile, "from_server"))

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    print('Cliente desconectado')

def main():
    if len(sys.argv) != 5:
        print('Uso: ' + sys.argv[0] + ' port-in host port-out file')
        sys.exit(1)

    portin = sys.argv[1]
    host = sys.argv[2]
    portout = sys.argv[3]
    logfile = sys.argv[4]

    s = jsockets.socket_tcp_bind(portin)

    if s is None:
        print('Bind falló')
        sys.exit(1)

    while True:
        conn, addr = s.accept()
        pid = os.fork()
        if pid == 0:  # Proceso hijo
            s.close()  # Cerramos el socket que no vamos a usar en el hijo
            proxy(conn, host, portout, logfile)
            sys.exit(0)
        else:
            conn.close()  # Cerramos el socket que no vamos a usar en el padre

if __name__ == "__main__":
    main()
