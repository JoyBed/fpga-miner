import socket
import time
from serial import Serial

def receive_data(conn):
    data = conn.recv(1024).decode().strip()
    if data == "":
        print("Lost connection to pool")
        exit()

    # Process the received data
    process_data(conn, data)

def send_response(conn, nonce, idstring, ntime, nonce2):
    work_submit = "submit_nonce " + nonce + " " + idstring + " " + ntime + " " + nonce2
    conn.send(work_submit.encode())
    print("Data sent back to pool: ", work_submit.encode())
    print("End work ---------------------------------------------------------------------------------------------")

def process_work(conn, data, target, seed, idstring, ntime, nonce2):
    ser = Serial("/dev/ttyUSB2", 115200, timeout=2)
    bit_width = len(data) * 4 
    binary_data = format(int(data, 16), f"0{bit_width}b")
    reversed_data = (binary_data[::-1])
    hex_data = hex(int(reversed_data, 2))[2:]
    data_reversed = bytearray.fromhex(data)[::-1]
    data_hex_reversed = data_reversed.hex()
    #payload1 = hex_data.zfill(160) + target[4:-36]
    #payload1 = data[:-8] + target
    hex_bytes = bytes.fromhex(data[:-8])
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
            nonce_temp = y
            prev = y
            result = 1
        elapsed_time = time.time() - start_time
        if elapsed_time > (5 * 60):
            result = 0
            waiting = 0
            
    if (result == 1):
        nonce_res = nonce_temp.hex()
        print("Received data from FPGA")
        print("Nonce: ", nonce_res)
        print(nonce_res)
        nonce_res2 = hex(int(nonce_res, 16) - int("0", 16))
        print(nonce_res2[2:])
        nonce_temp2 = nonce_res2[2:]
        nonce = nonce_temp2.rjust(8, '0')
        print(type(nonce), nonce)
        print(nonce_temp2)
        send_response(conn, nonce, idstring, ntime, nonce2)
    else:
        print("No data received from FPGA")
        print("Jumping back to receiving work")
        return

def process_data(conn, data):
    # Process the received data based on the expected format
    # Adjust this function to handle the specific data format used by the proxy
    # Replace the print statements with your desired logic

    # Assuming each command is on a new line
    lines = data.split("\n")
    for line in lines:
        if line.startswith("connected"):
            handle_connected(conn, line)
        elif line.startswith("set_target"):
            handle_set_target(line)
        elif line.startswith("work"):
            handle_work(conn, line)
        elif line.startswith("result"):
            handle_result(line)
        elif line.startswith("reconnect"):
            handle_reconnect(line)
        elif line.startswith("authorized"):
            print("Mining authorized")
        elif line.startswith("set_subscribe_params"):
            handle_subscribe(conn, line)
        else:
            print("Unknown command:", line)

def handle_subscribe(conn, line):
    print(line)
    print("Getting authorisation...")
    auth = "auth JoyBed.worker1"
    conn.send(auth.encode())

def handle_connected(conn, line):
    # Process the connected command
    # Extract necessary information from the line if needed
    print("Connected to pool:", line)

def handle_set_target(line):
    # Process the set_target command
    # Extract necessary information from the line if needed
    print("Pool target:", line)

def handle_work(conn, line):
    # Process the work command
    # Extract necessary information from the line if needed
    #print("Received data: ", line)
    parts = line.split(" ")
    if len(parts) == 7:
        data = parts[1]
        target = parts[2]
        seed = parts[3]
        idstring = parts[4]
        ntime = parts[5]
        nonce2 = parts[6]
        print("New work ---------------------------------------------------------------------------------------------")
        print("Data: ", data)
        print("Target: ", target)
        print("Seed: ", seed)
        process_work(conn, data, target, seed, idstring, ntime, nonce2)

def handle_result(line):
    # Process the result command
    # Extract necessary information from the line if needed
    parts = line.split(" ")
    if len(parts) == 2:
        status = parts[1]
        #process_result(status)
        print("Status: ", status)

def handle_reconnect(line):
    # Process the reconnect command
    # Extract necessary information from the line if needed
    print("Reconnect request received, clearing work")
    #clear_work()

def create_proxy_conn():
    # Create a TCP socket connection to the proxy
    print("Connecting to proxy...")
    proxy_host = "127.0.0.1"
    proxy_port = 17065
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((proxy_host, proxy_port))
    return conn

# Main entry point
def main():
    conn = create_proxy_conn()
    while(True):
        receive_data(conn)

if __name__ == "__main__":
    main()
