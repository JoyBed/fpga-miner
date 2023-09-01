from serial import Serial

def main():
    ser = Serial("/dev/ttyUSB2", 115200, timeout=20)
    #target = '000000000ffff000000000000000000000000000000000000000000000000000'
    target = '000000000ffff000000000000000000000000000000000000000000000000000'
    #target = '0123F56789ABCDEF0123456789AFCDEF0123456789ABCDEF0123456789ABCDEF'
    #data = 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
    data = '1b01518c64e486187b6ee8afd7ed8553af3ae05421c002350d050344018fe3d5f9c8b33ae13a8a1e07c6e061874ff45435dbf810f04f0dc1274fb58757b585afa48ee77b52ca284a20000e02'
    payload1 = data + target[4:-36]
    payload = bytes.fromhex(payload1)
    print(payload1)
    ser.write(payload)
    prev = None
    while(True):
        #x = ser.read(4)
        x = ser.readline()
        y = x[:-1]
        if (y != prev) and (y != b'') and (len(y) != 8):
            print(y.hex())
            prev = y

if __name__ == "__main__":
    main()
    
#expected result is probably 13c97c28 or D2B9FFD1
