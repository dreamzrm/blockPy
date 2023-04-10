!pip install cryptography
from os import times, times_result
import pickle
import time
import random
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


if __name__=="__main__":
    pr1, pu1=generate_keys()
    pr2, pu2=generate_keys() 
    pr3, pu3=generate_keys()

    
    Tx1 = Tx()
    Tx1.add_input(pu1, 1)
    Tx1.add_output(pu2, 1)
    Tx1.sign(pr1)
    

    if Tx1.is_valid():
        print("Success! Tx is valid")

    message = b"Tx1"
    sig = sign(message, pr1)
    print(verify(message, sig, pu1))

    
    #pu_ser = pu1.public_bytes(
    #encoding=serialization.Encoding.PEM,
    #format=serialization.PublicFormat.SubjectPublicKeyInfo
#)
    addrfile = open("public.dat", "wb")
    pickle.dump(pu1, addrfile)
    addrfile.close()
    savefile= open("tx.dat", "wb")
    pickle.dump(Tx1, savefile)
    savefile.close()

    loadfile = open("tx.dat", "rb")
    new_pu = pickle.load(loadfile)
    #loaded_pu = serialization.load_pem_private_key(
    #    new_pu
    #)
    print(verify(message, sig,new_pu))
    loadfile.close()

    loadfile = open("tx.dat", "rb")
    newTx = pickle.load(loadfile)

    if newTx.is_valid():
        print("Success! Loaded tx is valid")
    loadfile.close()

    root= TxBlock(None)
    root.addtx(Tx1)

    Tx2= Tx()
    Tx2.add_input(pu2, 1.1)
    Tx2.add_output(pu3, 1)
    Tx2.sign(pr2)
    root.addtx(Tx2)

    B1= TxBlock(root)
    Tx3= Tx()
    Tx3.add_input(pu3, 1.1)
    Tx3.add_output(pu1, 1)
    Tx3.sign(pr3)
    root.addtx(Tx3)

    Tx4= Tx()
    Tx4.add_input(pu1, 1)
    Tx4.add_output(pu2, 1)
    Tx4.add_reqd(pu3)
    Tx4.sign(pr1)
    Tx4.sign(pr3)
    B1.addtx(Tx4)
    
    start = time.time()
    print(B1.find_nonce())
    elapsed = time.time() - start
    print("Elapsed time: "+ str(elapsed)+ "s.")
    if elapsed < 60:
        print("Error! Mining is too fast!")
    if B1.good_nonce():
        print("Success! Nonce is good!")
    else:
        print("Error! Bad nonce")
    

    B1.is_valid()
    root.is_valid()

    savefile = open("block.dat", "wb")
    pickle.dump(B1, savefile)
    savefile.close()


    loadfile = open("block.dat", "rb")
    load_B1 =  pickle.load(loadfile)

    print(bytes(str(load_B1.data), 'utf-8'))

    load_B1.is_valid()
    for b in [root, B1, load_B1, load_B1.previousBlock]:
        if b.is_valid():
            print("Success! Valid block")
        else:
            print("Error! Bad block")

    if B1.good_nonce():
        print("Success! Nonce is good after save and load!")
    else:
        print("Error! Bad nonce after load!")

    B2= TxBlock(B1)
    Tx5 = Tx()
    Tx5.add_input(pu3, 1)
    Tx5.add_output(pu1, 100)
    Tx5.sign(pr3)
    B2.addtx(Tx5)
    print(Tx5.is_valid())

    load_B1.previousBlock.addtx(Tx4)
    for b in [B2, load_B1]:
        if b.is_valid():
            print ("Error! Bad block verified")
        else:
            print("Success! Bad blocks detected")
  
    pr4, pu4 = generate_keys()
    B3 = TxBlock(B2)
    B3.addtx(Tx2)
    B3.addtx(Tx3)
    B3.addtx(Tx4)
    Tx6 = Tx()
    Tx6.add_output(pu4, 25)
    B3.addtx(Tx6)
    if B3.is_valid():
        print("Success! Bad block detected.")
    else:
        print("Error! Block reward fails.")
    
    B4 = TxBlock(B3)
    B4.addtx(Tx2)
    B4.addtx(Tx3)
    B4.addtx(Tx4)
    Tx7 = Tx()
    Tx7.add_output(pu4, 25.1)
    B4.addtx(Tx7)
    if B4.is_valid():
        print("Success! Tx fees succeeds.")
    else:
        print("Error! Tx feesBlock fails.")

    #Greedy miner
    B5 = TxBlock(B4)
    B5.addtx(Tx2)
    B5.addtx(Tx3)
    B5.addtx(Tx4)
    Tx8 = Tx()
    Tx8.add_output(pu4, 26.2)
    B5.addtx(Tx8)
    if not B5.is_valid():
        print("Success! Greedy miner detected.")
    else:
        print("Error! Greedy miner not detected.")

    