#!pip install cryptography
from os import times, times_result
import pickle
import time
import random
import socket
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

reward = 25.0
leading_zeros = 1
next_char_limit = 50

class CBlock:
    data = None
    previousHash = None
    previousBlock = None
    def __init__(self, data, previousBlock):
        self.data = data
        self.previousBlock = previousBlock
        if previousBlock != None:
            self.previousHash = previousBlock.computeHash()
    def computeHash(self):
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(bytes(str(self.data),'utf8'))
        digest.update(bytes(str(self.previousHash),'utf8'))
        return digest.finalize()
    def is_valid(self):
        if self.previousBlock == None:
            return True
        return self.previousBlock.computeHash() == self.previousHash


def generate_keys():
    private = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )    
    public = private.public_key()#hash the private key to get the public key
    pu_ser = public.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private, pu_ser

def sign(message, private):
    message = bytes(str(message), 'utf-8')
    sig = private.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return sig

def verify(message, sig, pu_ser):
    public = pu_ser
    message = bytes(str(message), 'utf-8')
    try:
        public.verify(
            sig,
            message,
            padding.PSS(
              mgf=padding.MGF1(hashes.SHA256()),
              salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except InvalidSignature:
        return False
    except:
        print("Error executing public_key.verify")
        return False
    
class Tx:
    inputs = None
    outputs =None
    sigs = None
    reqd = None
    def __init__(self):
        self.inputs = []
        self.outputs = []
        self.sigs = []
        self.reqd = []
    def add_input(self, from_addr, amount):
        self.inputs.append((from_addr, amount))
    def add_output(self, to_addr, amount):
        self.outputs.append((to_addr, amount))
    def add_reqd(self, addr):
        self.reqd.append(addr)
    def sign(self, private):
        message = self.__gather()
        newsig = sign(message, private)
        self.sigs.append(newsig)        
    def __gather(self):
        data=[]
        data.append(self.inputs)
        data.append(self.outputs)
        data.append(self.reqd)
        return data
    def __repr__(self):
        reprstr = "INPUTS:"
        for addr, amt in self.inputs:
            reprstr = reprstr + str(amt) + "from" + str(addr)
        reprstr = reprstr + "OUTPUTS:\n"
        for addr, amt in self.outputs:
             reprstr = reprstr + "REQD:\n"
        reprstr = reprstr + "REQD:\n"
        for r in self.reqd:
            reprstr = reprstr + str(r) + "\n"
        reprstr = reprstr + "SIGS:\n"
        for s in self.sigs:
            reprstr = reprstr + str(s) + "\n"
        reprstr = reprstr + "END\n"
        return reprstr
    def is_valid(self):
        total_in = 0
        total_out = 0
        message = self.__gather()
        for addr,amount in self.inputs:
            found = False
            for s in self.sigs:
                if verify(message, s, addr) :
                    found = True
            if not found:
                print ("No good sig found for " + str(message))
                return False
            if amount < 0:
                return False
            total_in = total_in + amount
        for addr in self.reqd:
            found = False
            for s in self.sigs:
                if verify(message, s, addr) :
                    found = True
            if not found:
                return False
        for addr,amount in self.outputs:
            if amount < 0:
                return False
            total_out = total_out + amount


class TxBlock (CBlock):
     nonce='AAAAAA'
     def __init__(self, previousBlock):
        super(TxBlock, self).__init__([], previousBlock)
     def addtx(self, Tx_in):
         self.data.append(Tx_in)
     def __count__totals(self):
         total_in=0
         total_out=0
         for tx in self.data:
             for addr, amt in tx.inputs:
                 total_in =total_in + amt
             for addr, amt in tx.outputs:
                 total_out = total_out + amt
         return total_in, total_out
     def is_valid(self):
         if not super(TxBlock, self).is_valid():
             return False
         for tx in self.data:
             if not tx.is_valid():
                 return False
         total_in, total_out = self.__count__totals()
         if total_out - total_in - reward > 0.00000000000000001:
             return False
         return True
     def good_nonce(self):
         digest = hashes.Hash(hashes.SHA256())
         digest.update(bytes(str(self.data),'utf8'))
         digest.update(bytes(str(self.previousHash),'utf8'))
         digest.update(bytes(str(self.nonce),'utf8'))
         this_hash = digest.finalize()
         print(this_hash[:leading_zeros])
         #if this_hash[:leading_zeros] != bytes(''.join['\x4f' for i in range(leading_zeros)], 'utf8'):
             #return False
         #return int(this_hash[leading_zeros]) < next_char_limit
     def find_nonce(self):
         for i in range(100000):
             self.nonce = ''.join([
                 chr(random.randint(0,255)) for i in range(10*leading_zeros)])
             if self.good_nonce():
                 return self.nonce
         return None

TCP_PORT = 5005
BUFFER_SIZE = 1024

def recvObj(ip_addr):
    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ip_addr, TCP_PORT))
    s.listen()
    new_sock, addr=s.accept()
    all_data =b''
    while True:
        data = new_sock.recv(BUFFER_SIZE)
        if not data: break
        all_data = all_data + data
    return pickle.loads(all_data)

if __name__=="__main__":
    newB = recvObj('localhost')
    print (newB.data[0])
    print (newB.data[1])
    if (newB.is_valid()):
        print("Success! Tx is valid!")
    else:
        print ("Error! Tx invalid")
    if(newB.data[0].inputs[0][1]==2.3):
        print("Success! Input value matches")
    else:
        print("Error! Wrong input value")
    if(newB.data[0].outputs[0][1]==2.3):
        print("Success! Output value matches")
    else:
        print("Error! Wrong Output value")
    if(newB.data[1].outputs[0][1]==3.1):
        print("Success! Output value matches")
    else:
        print("Error! Wrong Output value")
    if(newB.data[1].outputs[1][1]==1.0):
        print("Success! Output value matches")
    else:
        print("Error! Wrong Output value")
    newTx = recvObj('localhost')
    print (newTx)