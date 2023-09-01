import socket
import json
import hashlib
import binascii
from pprint import pprint
import time
import random
from serial import Serial

address = 'DAXhPVeS94RvKgJNx6s4YD5EAt26rZSnNX'

host    = 'dgbodo.stratum.hashpool.site'
port    = 11116

print("address:{}".format(address))
print("host:{} port:{}".format(host,port))

sock    = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((host,port))

#server connection
sock.sendall(b'{"id": 1, "method": "mining.subscribe", "params": []}\n')
response = json.loads(sock.recv(1024))
print(response)
sub_details,extranonce1,extranonce2_size = response['result']

#authorize workers
sock.sendall(b'{"params": ["DAXhPVeS94RvKgJNx6s4YD5EAt26rZSnNX", "x"], "id": 2, "method": "mining.authorize"}\n')


while(True):
    response = ''
    response = sock.recv(1024)
    print(response)
    response = ''
    response = sock.recv(1024)
    print(response)
    
    #get rid of empty lines
    responses = [json.loads(res) for res in response.split(b'\n') if len(res.strip()) > 0]
    
    pprint(responses)
    #welcome message
    #print responses[0]['params'][0]+'\n'
    
    
    job_id,prevhash,coinb1,coinb2,merkle_branch,version,nbits,ntime,clean_jobs \
        = responses[1]['params']

    #target http://stackoverflow.com/a/22161019
    target = (nbits[2:]+'00'*(int(nbits[:2],16))).zfill(64)
    print('target:{}\n'.format(target))
    
    extranonce2 = '00'*extranonce2_size
    
    coinbase = coinb1 + extranonce1 + extranonce2 + coinb2
    coinbase_hash_bin = hashlib.sha256(hashlib.sha256(binascii.unhexlify(coinbase)).digest()).digest()
    
    print('coinbase:\n{}\n\ncoinbase hash:{}\n'.format(coinbase,binascii.hexlify(coinbase_hash_bin)))
    merkle_root = coinbase_hash_bin
    for h in merkle_branch:
        merkle_root = hashlib.sha256(hashlib.sha256(merkle_root + binascii.unhexlify(h)).digest()).digest()
    
    merkle_root = binascii.hexlify(merkle_root)
    
    #little endian
    merkle_root = b''.join([merkle_root[i:i+2] for i in range(0, len(merkle_root), 2)][::-1]).decode('utf-8')
    
    print('merkle_root:{}\n'.format(merkle_root))
       
    blockheader = version + prevhash + merkle_root + nbits + ntime + "00000000"
    
    print('blockheader:\n{}\n'.format(blockheader))
    
    #add FPGA mining part
    ser = Serial("/dev/ttyUSB2", 115200, timeout=2)
    hex_bytes = bytes.fromhex(blockheader[:-8])
    reversed_bytes = hex_bytes[::-1]
    reversed_hex_data = reversed_bytes.hex()
    payload1 = reversed_hex_data + target[4:-36]
    #payload1 = blockheader[:-8] + target[4:-36]
    payload = bytes.fromhex(payload1)
    print("Sent to FPGA: ", payload.hex())
    ser.write(payload)
    
    start_time = time.time()
    result = 0
    waiting = 1
    prev = None
    while(waiting):
        x = ser.readline()
        y = x[:-1]
        if (y != prev) and (y != b'') and (len(y) != 8):
            waiting = 0
            nonce = y
            prev = y
            result = 1
        elapsed_time = time.time() - start_time
        if elapsed_time > (210):
            result = 0
            waiting = 0
        
    if (result == 1):
        print("Received data from FPGA")
        print("Nonce: ", (nonce.hex()))
    else:
        print("No data received from FPGA")
        print("Jumping back to receiving work")

    noncehex = nonce.hex()

    answer = '{"params": ["'+address+'", "'+job_id+'", "'+extranonce2 \
        +'", "'+ntime+'", "'+noncehex+'"], "id": 1, "method": "mining.submit"}\n'
    sock.sendall(answer.encode())
    print(sock.recv(1024))

sock.close()

