import socket
import sys
import json
import header
from binascii import hexlify, unhexlify
from hashlib import sha256
from struct import pack
sys.path.append("../solo/")
from template import sha256d, merkle_root, merkle_branch, serialize_int

# Pool details
pool_host = "dgbodo.stratum.hashpool.site"
pool_port = 11116  # Replace with your pool's port

# Worker details
worker_username = "DAXhPVeS94RvKgJNx6s4YD5EAt26rZSnNX"
worker_password = "x"

nonce2 = 0
# Create a socket connection to the pool
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((pool_host, pool_port))

    # Send a mining subscribe request
    subscribe_request = b'{"id": 1,"method": "mining.subscribe","params": ["odominer"]}\n'
    s.send(subscribe_request)

    response = s.recv(1024).decode()
    response_json = json.loads(response)
    print(response)

    if 'result' in response_json and len(response_json['result']) > 1:
        enonce1 = response_json['result'][1]
        nonce2len = response_json['result'][2]
        print(f"Subscribed to mining notifications. Extranonce1: {enonce1}")

    # Send a mining authorize request
    authorize_request = b'{"id": 2,"method": "mining.authorize","params": ["DAXhPVeS94RvKgJNx6s4YD5EAt26rZSnNX", "x"]}\n'
    s.send(authorize_request)

    response = s.recv(4096).decode()
    response_json = json.loads(response)
    print(response_json)

    if 'result' in response_json and response_json['result'] is True:
        print(f"Authorized as worker: {worker_username}")

    # Listen for mining notifications and extract data
    
        buffer = ""
    while True:
        data = s.recv(4096).decode()
        buffer += data

        # Split received data into individual JSON objects
        while '\n' in buffer:
            line, buffer = buffer.split('\n', 1)
            if line.strip():
                mining_notification_json = json.loads(line)
                print("Received JSON object: ", mining_notification_json)

                # Process the JSON object here
                if 'method' in mining_notification_json:
                    method = mining_notification_json['method']
                    if method == 'mining.notify':
                        # Extract relevant data and perform mining tasks
                        job_id = mining_notification_json['params'][0]
                        ntime = mining_notification_json['params'][7]
                        idstring  = mining_notification_json['params'][0]
                        prevhash  = header.swap_order(mining_notification_json['params'][1][::-1])
                        coinbase1 = mining_notification_json['params'][2]
                        coinbase2 = mining_notification_json['params'][3]
                        merklearr = mining_notification_json['params'][4]
                        version   = int(mining_notification_json['params'][5], 16)
                        bits      = mining_notification_json['params'][6]
                        curtime   = int(mining_notification_json['params'][7], 16)
                        # Extract other data as needed
                        print(f"\nidstring: {idstring}\n prevhash: {prevhash}\n coinbase1: {coinbase1}\n coinbase2: {coinbase2}\n merklearr: {merklearr}\n version: {version}\n bits: {bits}\n curtime: {curtime}\n")
                        
                        if mining_notification_json['params'][8] and nonce2 > 0:
                            nonce2 = 0
                        else:
                            nonce2 += 1
                        
                        nonce2hex1 = hex(nonce2)
                        nonce2hex = nonce2hex1[2:]
                        
                        # Pad with zeros if needed to match nonce2len * 2 characters
                        while len(nonce2hex) < (nonce2len - 1) * 2:
                            nonce2hex = '0' + nonce2hex
                        
                        coinbasehex = coinbase1+enonce1+nonce2hex+coinbase2
                        # Convert the hexadecimal string to bytes
                        coinbasebytes = unhexlify(coinbasehex)

                        # Calculate the double SHA-256 hash
                        coinbasetxid = sha256(sha256(coinbasebytes).digest()).digest()
                        
                        data = pack('<I', version)
                        data += unhexlify(prevhash)[::-1]
                        data += header.build_merkle_root(coinbasetxid, merklearr)
                        data += pack('<I', curtime)
                        data += unhexlify(bits)[::-1]
                        data += b'\0\0\0\0' # nonce

                        b_header = str(hexlify(data))
                        print("Header: ", b_header)

    

#except Exception as e:
#    print(f"An error occurred: {str(e)}")
finally:
    s.close()
