#!/usr/bin/env python

import sys
from binascii import hexlify, unhexlify
from hashlib import sha256
from struct import pack

def swap_order(d, wsz=8, gsz=1 ):
    return "".join(["".join([m[i:i+gsz] for i in range(wsz-gsz,-gsz,-gsz)]) for m in [d[i:i+wsz] for i in range(0,len(d),wsz)]])

def build_merkle_root(coinbase_hash_bin, merkle_b):
    merkle_r = coinbase_hash_bin
    for h in merkle_b:
        merkle_r = sha256d(merkle_r + unhexlify(h))
    return merkle_r

def odokey_from_ntime(curtime, testnet):
    if testnet:
        nOdoShapechangeInterval = 1*24*60*60     # 1 days, testnet
    else:
        nOdoShapechangeInterval = 10*24*60*60    # 10 days, mainnet
    ntime = int(curtime, 16)
    odokey  = ntime - ntime % nOdoShapechangeInterval
    return odokey

def difficulty_to_hextarget(difficulty):
    assert difficulty >= 0
    if difficulty == 0: return 2**256-1
    target = min(int((0xffff0000 * 2**(256-64) + 1)/difficulty - 1 + 0.5), 2**256-1)
    targethex = hex(target).rstrip("L").lstrip("0x")
    targetstr = '0'* (64 - len(targethex)) + targethex
    return str(targetstr)
    
def sha256d(data):
    return sha256(sha256(data).digest()).digest()
