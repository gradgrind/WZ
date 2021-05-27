# -*- coding: utf-8 -*-
"""
Created on Wed May 26 10:38:03 2021

@author: mt
"""

from base64 import b64encode, b64decode
import io

def ipack(item, itype):
    if itype == 'INT':
        return b'INT$' + str(item).encode('utf-8')
    if itype == 'STR':
        return b'STR$' + b64encode(item.encode('utf-8'))
    if itype == 'LIST':
        x = b';'.join(ipackx(item))
        return b'[{x}]'

print(ipack(23, 'INT'))
print(ipack("§ABC€", 'STR'))

f = io.BytesIO(b"some initial binary data: \x00\x01")

_L0 = b'['
_L1 = b']'
_D0 = b'{'
_D1 = b'}'
_B0 = b'*'
def parse(bstring):
    obj = [[_B0]]
    stack = []
    bs = io.BytesIO(bstring)
    x = []
    while True:
        b = bs.read(1)
        if not b: break
        if b == _L0:
            if x:
                raise Fail("Unexpected [")
            stack.append([_L0])
            obj[-1].append([_L0])
            
        elif b == _L1:
            try:
                if stack.pop() == _L0:
                    obj[-1].append
                        
            else:
                raise Fail("], but not reading list")
        elif b == _D0:
            stack.append([_D0])
            
        elif b == _D1:
    
    
    if stack:
        print("Unmatched brackets", stack)
    else:
        
