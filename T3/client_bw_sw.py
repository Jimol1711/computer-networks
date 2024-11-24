#!/usr/bin/python3
# Echo client program que mide ancho de banda
# Version con dos threads: uno lee de stdin hacia el socket y el otro al revés
import jsockets
import sys, threading
import time

# command for running the script:
# ./client_bw_sw.py 15 127.0.0.1 1818 < 05MbA.txt > OUT

PACK_SZ=1500
MAX_SEQ=65535
eof=0
tout=0.5
rtt=0.5
ack = 1

def Rdr(s, mutex):
    global ack, rtime
    sz = 0
    ack = 1
    next_seq = 0
    errs=0
    while True:
        try:
            #print(f'al rev, {eof}, {sz}', file=sys.stderr)
            data=s.recv(PACK_SZ+2)
            #print(f'del rev, {len(data)}', file=sys.stderr)
        except:
            data = None
        if not data:
            break
        seq = int.from_bytes(data[0:2], 'big')
        if seq == next_seq:
            with mutex:
                #print(f'rcv: recibo {seq}', file=sys.stderr)
                ack = seq
                rtime = time.time()
                mutex.notify()
            if len(data[2:]) == 0: # EOF
                break
            sys.stdout.buffer.write(data[2:])
            sz += len(data[2:])
            next_seq = (next_seq+1)%(MAX_SEQ+1)
            # print(f'rcv: {sz}, {len(data)}, {seq}', file=sys.stderr)
        else:
            errs+=1

    print(f'Rcvr: errs={errs}', file=sys.stderr)

if len(sys.argv) != 4:
    print('Use: '+sys.argv[0]+' size host port', file=sys.stderr)
    sys.exit(1)

PACK_SZ = int(sys.argv[1])
s = jsockets.socket_udp_connect(sys.argv[2], sys.argv[3])
if s is None:
    print('could not open socket', file=sys.stderr)
    sys.exit(1)

print(s.getsockname(), file=sys.stderr)
print(f'Usando pack_sz = {PACK_SZ}', file=sys.stderr)

mutex = threading.Condition()
# Creo thread que lee desde el socket hacia stdout:
newthread = threading.Thread(target=Rdr, args=(s, mutex))
newthread.start()

# En este otro thread leo desde stdin hacia socket:
sz = 0
seq = 0
eof = False
errs=0
while not eof:
    data = sys.stdin.buffer.read(PACK_SZ)
    if not data:
        eof = True
    tries=0
    while True:
        stime=time.time()
        time.sleep(0.05)
        if not eof:
            s.send(seq.to_bytes(2, 'big')+data)
        else:
            s.send(seq.to_bytes(2, 'big'))
        # if seq % 100 == 0:
        print(f'snd: {seq}, t_out: {tout}', file=sys.stderr)
        # Esperamos ACK
        print("expected: ", ack, file=sys.stderr)
        with mutex:
            mutex.wait(tout)
            # print(f'snd: {seq}, {ack}', file=sys.stderr)
            if ack == seq:
                if tries == 0:
                    rtt = rtime-stime
                    tout = rtt*3
                break
            else:
                errs+=1
                tries+=1

    sz += len(data)
    seq = (seq+1)%(MAX_SEQ+1)

newthread.join()
print(f'Sndr: errs={errs}', file=sys.stderr)
s.close()
