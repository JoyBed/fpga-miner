import socket
import sys
import json
import header
import time
from binascii import hexlify, unhexlify
from hashlib import sha256
from struct import pack
from serial import Serial

# Pool details
pool_host = "dgb-odocrypt.f2pool.com"
#pool_host = "odocrypt.eu.mine.zpool.ca"
#pool_host = "europe.solomining.io"
pool_port = 11115  # Replace with your pool's port
#pool_port = 3331  # Replace with your pool's port
#pool_port = 8883  # Replace with your pool's port

# Worker details
worker_username = "DAXhPVeS94RvKgJNx6s4YD5EAt26rZSnNX"
worker_password = "d=0.03"

nonce2 = 0
# Create a socket connection to the pool
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((pool_host, pool_port))
    ser = Serial("/dev/ttyUSB2", 115200, timeout=2)

    cli_authid = "DAXhPVeS94RvKgJNx6s4YD5EAt26rZSnNX"

    # Send a mining subscribe request
    subscribe_request = b'{"id": 1,"method": "mining.subscribe","params": []}\n'
    s.send(subscribe_request)

    response = s.recv(1024).decode()
    response_json = json.loads(response)
    print(response)

    if 'result' in response_json and len(response_json['result']) > 1:
        enonce1 = response_json['result'][1]
        nonce2len = response_json['result'][2]
        print(enonce1)
        print(nonce2len)
        print(f"Subscribed to mining notifications. Extranonce1: {enonce1}")

    # Send a mining authorize request
    authorize_request = b'{"id": 2,"method": "mining.authorize","params": ["DAXhPVeS94RvKgJNx6s4YD5EAt26rZSnNX", "d=0.03"]}\n'
    s.send(authorize_request)

    # Listen for mining notifications and extract data
    
    buffer = ""
    #cli_jsonid = 3
    cli_jsonid = 3
    target = None
    authorised = False
    while True:
        data = s.recv(4096).decode()
        buffer += data

        # Split received data into individual JSON objects
        while '\n' in buffer:
            line, buffer = buffer.split('\n', 1)
            if line.strip():
                mining_notification_json = json.loads(line)
                #print("Received JSON object: ", mining_notification_json)

                # Process the JSON object here
                if 'method' in mining_notification_json:
                    method = mining_notification_json['method']
                    #print(mining_notification_json)
                    if method == 'mining.notify' and authorised == True:
                    
                        # Extract relevant data and perform mining tasks
                        job_id = idstring = mining_notification_json['params'][0]
                        prevhash  = header.swap_order(mining_notification_json['params'][1][::-1])
                        coinbase1 = mining_notification_json['params'][2]
                        coinbase2 = mining_notification_json['params'][3]
                        merklearr = mining_notification_json['params'][4]
                        version   = int(mining_notification_json['params'][5], 16)
                        bits      = mining_notification_json['params'][6]
                        curtime   = int(mining_notification_json['params'][7], 16)
                        ntime = mining_notification_json['params'][7]
                        
                        if 'odokey' in mining_notification_json:
                            odokey = mining_notification_json['odokey']
                        else:
                            odokey = header.odokey_from_ntime(str(ntime), 0)
                            
                        # Extract other data as needed
                        print(f"\n idstring: {idstring}\n prevhash: {prevhash}\n coinbase1: {coinbase1}\n coinbase2: {coinbase2}\n merklearr: {merklearr}\n version: {version}\n bits: {bits}\n curtime: {curtime}\n odokey: {odokey}\n")
                        
                        if mining_notification_json['params'][8] and nonce2 > 0:
                            nonce2 = 0
                        else:
                            nonce2 += 1
                        
                        nonce2hex1 = hex(nonce2)
                        nonce2hex = nonce2hex1[2:]
                        
                        # Pad with zeros if needed to match nonce2len * 2 characters
                        while len(nonce2hex) < (nonce2len) * 2:
                            nonce2hex = '0' + nonce2hex
                        
                        coinbasehex = coinbase1+enonce1+nonce2hex+coinbase2
                        
                        # Convert the hexadecimal string to bytes
                        coinbasebytes = unhexlify(coinbasehex)

                        # Calculate the double SHA-256 hash
                        coinbasetxid = header.sha256d(coinbasehex.encode())
                        
                        data = pack('<I', version)
                        data += unhexlify(prevhash)[::-1]
                        data += header.build_merkle_root(coinbasetxid, merklearr)
                        data += pack('<I', curtime)
                        data += unhexlify(bits)[::-1]
                        data += b'\0\0\0\0' # nonce

                        b_header = str(hexlify(data))
                        print("Header: ", b_header[2:-1])
                        
                        #print(data)
                        hex_bytes = bytes.fromhex(str(b_header[2:-1])[:-8])
                        reversed_bytes = hex_bytes[::-1]
                        reversed_hex_data = reversed_bytes.hex()
                        payload1 = reversed_hex_data + target[4:-36]
                        payload = bytes.fromhex(payload1)
                        
                        print("Data sent to FPGA")
                        print("Sent to FPGA: ", payload.hex())
                        ser.read(1000) # just to flush the buffer
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
                            if elapsed_time > (240):
                                result = 0
                                waiting = 0
            
                        if (result == 1):
                            print("Received data from FPGA")
                            print("Nonce: ", (nonce.hex()))
                            params = [cli_authid, str(idstring), str(nonce2hex), str(ntime), str(nonce.hex())]
                            modifiedchunk = json.dumps({'id':cli_jsonid, 'method':'mining.submit','params':params})
                            print(modifiedchunk)
                            s.send(modifiedchunk.encode())
                            cli_jsonid += 1
                        else:
                            print("No data received from FPGA")
                            print("Jumping back to receiving work")

                    elif method == 'mining.set_difficulty':
                        cli_diff = float(mining_notification_json['params'][0])
                        target = header.difficulty_to_hextarget(cli_diff)
                        print('\nTarget: {}'.format(target))
                        
                elif 'reject-reason' in mining_notification_json:
                    print(mining_notification_json)
                    
                elif 'result' in mining_notification_json:
                    #print(mining_notification_json)
                    if (mining_notification_json['result'] is True) and (mining_notification_json['id'] == int(2)):
                        authorised = True
                        print(f"Authorized as worker: {worker_username}")
                    elif (mining_notification_json['result'] is True) and (mining_notification_json['id'] != int(2)):
                        print(type(mining_notification_json['id']))
                        print(mining_notification_json['result'])
                        print("Result accepted")
                else:
                    print(mining_notification_json)
                    

finally:
    s.close()
