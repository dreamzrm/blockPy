from os import times
from Blockchain import CBlock 
from Signatures import generate_keys, sign, verify
from Transactions import Tx
import pickle
import time
import Transactions
import random
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
reward = 25.0
leading_zeros = 19
next_char_limit = 255

class TxBlock (CBlock):
     nonce='AAAAAA'
     def __init__(self, previousBlock):
        super(TxBlock, self).__init__([], previousBlock)
     def addtx(self, Tx_in):
         self.data.append(Tx_in)
     def removeTx(self, Tx_in):
         if Tx_in in self.data:
             self.data.remove(Tx_in)
             return True
         return False
     def count__totals(self):
         total_in=0
         total_out=0
         for tx in self.data:
             for addr, amt, inx in tx.inputs:
                 total_in =total_in + amt
             for addr, amt in tx.outputs:
                 total_out = total_out + amt
         return total_in, total_out
     def check_size(self):
        savePrev = self.previousBlock
        self.previousBlock = None
        this_size = len(pickle.dumps(self))
        self.previousBlock = savePrev
        if this_size > 10000:
            return False
        return True
     def is_valid(self):
         if not super(TxBlock, self).is_valid():
             return False
         spends={}
         for tx in self.data:
             if not tx.is_valid():
                 return False
             for addr, amt, inx in tx.inputs:
                 if addr in spends:
                     spends[addr] = spends[addr]  + amt
                 else:
                     spends[addr] = amt
                 if not inx-1 == getLastTxIndex(addr, self.previousBlock):
                     found=False
                     count = 0
                     for tx2 in self.data:
                         for addr2, amt2, inx2 in tx2.inputs:
                             if addr == addr2 and inx2 == inx-1:
                                 found=True
                                 if addr== addr2 and inx2 == inx:
                                     count = count + 1
                     if not found or count > 1:
                         return False
             for addr, amt in tx.outputs:
                 if addr in spends:
                     spends[addr] = spends[addr]  - amt
                 else:
                     spends[addr] = -amt
         for this_addr in spends:
             verbose = True
             if verbose: print("Balance: " + str(getBalance(this_addr, self.previousBlock)))
             if verbose: print("Spends: " + str(spends[this_addr]))
             if spends[this_addr] - getBalance(this_addr, self.previousBlock) > 0.0000001:
                 return False

            
         total_in, total_out = self.count__totals()
         if total_out - total_in - reward > 0.00000000000000001:
             return False
         if not self.check_size():
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
         return int(this_hash[leading_zeros]) < next_char_limit
     def find_nonce(self, n_tries=1000000):
         for i in range(n_tries):
             for i in range(10 * leading_zeros):
                # myList[i] = chr(random.randint(0, 255)) 
                #self.nonce = ''.join(myList)
                self.nonce = ''.join([ 
                   chr(random.randint(0,255)) for i in range(10*leading_zeros)])
             if self.good_nonce():
                 return self.nonce
         return None


def findLongestBlockchain(head_blocks):
    longest = -1
    long_head = None
    for b in head_blocks:
        current = b
        this_len = 0
        while current != None:
            this_len= this_len + 1
            current = current.previousBlock
        if this_len > longest:
            long_head = b
            longest = this_len
    return long_head

def saveBlocks(block_list, filename):
    fs = open(filename, "wb")
    pickle.dump(block_list, fs)
    fs.close()
    return True

def loadBlocks(filename):
    fin = open(filename, "rb")
    openFile = pickle.load(fin)
    fin.close() 
    return openFile
    
def getBalance(pu_key, last_block):
    this_block = last_block
    bal = 0.0
    while this_block != None:
        for tx in this_block.data:
            for addr, amt, inx in tx.inputs:
                if addr == pu_key:
                    bal=bal-amt
            for addr, amt in tx.outputs:
                if addr == pu_key:
                    bal=bal+amt
        this_block = this_block.previousBlock
    return bal

def getLastTxIndex(pu_key, last_block):
    this_block = last_block
    index = -1
    while this_block != None:
        for tx in this_block.data:
            for addr, amt, inx in tx.inputs:
                if addr == pu_key and inx > index:
                    index = inx
        if index != -1:
            break
        this_block = this_block.previousBlock
    return index

def processNewBlock(newBlock, head_blocks):
     verbose = True
     for b in head_blocks:
          if b == None:
            if newBlock.previousHash == None:
              found = True
              newBlock.previousBlock = b
              if not newBlock.is_valid():
                  if verbose : print("Error! newBlock is not valid")
              else:
               head_blocks.remove(b)
               head_blocks.append(newBlock)
               if verbose : print("Added to head blocks\n")
          elif newBlock.previousHash == b.computeHash():
            found  = True
            newBlock.previousBlock = b
            if not newBlock.is_valid():
                  if verbose : print("Error! newBlock is not valid")
            else:
             head_blocks.remove(b)
             head_blocks.append(newBlock)
             if verbose : print("Added to head blocks\n")
          else:
              this_block = b
              while this_block != None:
                  if newBlock.previoushash == this_block.previousHash:
                      found = True
                      newBlock.previousBlock = this_block.previousBlock
                      if not newBlock in head_blocks:
                          head_blocks.append(newBlock)
                          if verbose: print("Added new sister block")
                  this_block = this_block.previousBlock
          if not found:
              print("Error! Couldn't find a parent for newBlock")


if __name__=="__main__":
    pr1, pu1=generate_keys()
    pr2, pu2=generate_keys() 
    pr3, pu3=generate_keys()

    pu_indices = {}
    def indexed_input(Tx_inout, public_key, amt, index_map):
        if not public_key in index_map:
            index_map[public_key]=0
        Tx_inout.add_input(public_key, amt, index_map[public_key])
        index_map[public_key] = index_map[public_key] + 1
    
    Tx1 = Tx()
    indexed_input(Tx1, pu1, 1, pu_indices)
    Tx1.add_output(pu2, 1)
    Tx1.sign(pr1)
    

    if Tx1.is_valid():
        print("Success! Tx is valid")

    message = b"Tx1"
    sig = sign(message, pr1)
    print(verify(message, sig, pu1))

    
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
    mine1 = Tx()
    mine1.add_output(pu1, 8.0)
    mine1.add_output(pu2, 8.0)
    mine1.add_output(pu3, 8.0)

    root.addtx(Tx1)
    root.addtx(mine1)

    Tx2= Tx()
    indexed_input(Tx2, pu2, 1.1, pu_indices)
    Tx2.add_output(pu3, 1)
    Tx2.sign(pr2)
    root.addtx(Tx2)

    B1= TxBlock(root)
    Tx3= Tx()
    indexed_input(Tx3, pu3, 1.1, pu_indices)
    Tx3.add_output(pu1, 1)
    Tx3.sign(pr3)
    root.addtx(Tx3)

    Tx4= Tx()
    indexed_input(Tx4, pu1, 1, pu_indices)
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
    indexed_input(Tx5, pu3, 1, pu_indices)
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
  
    #Test mining rewards and tx fees 
    pr4, pu4 = generate_keys()
    Tx2= Tx()
    indexed_input(Tx2, pu2, 1.1, pu_indices)
    Tx2.add_output(pu3, 1)
    Tx2.sign(pr2)
    Tx3= Tx()
    indexed_input(Tx3, pu3, 1.1, pu_indices)
    Tx3.add_output(pu1, 1)
    Tx3.sign(pr3)
    Tx4= Tx()
    indexed_input(Tx4, pu1, 1, pu_indices)
    Tx4.add_output(pu2, 1)
    Tx4.add_reqd(pu3)
    Tx4.sign(pr1)
    Tx4.sign(pr3)
    B3 = TxBlock(B1)
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
    Tx2= Tx()
    indexed_input(Tx2, pu2, 1.1, pu_indices)
    Tx2.add_output(pu3, 1)
    Tx2.sign(pr2)
    Tx3= Tx()
    indexed_input(Tx3, pu3, 1.1, pu_indices)
    Tx3.add_output(pu1, 1)
    Tx3.sign(pr3)
    Tx4= Tx()
    indexed_input(Tx4, pu1, 1, pu_indices)
    Tx4.add_output(pu2, 1)
    Tx4.add_reqd(pu3)
    Tx4.sign(pr1)
    Tx4.sign(pr3)
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
    Tx2= Tx()
    indexed_input(Tx2, pu2, 1.1, pu_indices)
    Tx2.add_output(pu3, 1)
    Tx2.sign(pr2)
    Tx3= Tx()
    indexed_input(Tx3, pu3, 1.1, pu_indices)
    Tx3.add_output(pu1, 1)
    Tx3.sign(pr3)
    Tx4= Tx()
    indexed_input(Tx4, pu1, 1, pu_indices)
    Tx4.add_output(pu2, 1)
    Tx4.add_reqd(pu3)
    Tx4.sign(pr1)
    Tx4.sign(pr3)
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

    B6 = TxBlock(B4)
    this_pu = pu4
    this_pr = pr4
    #for i in range(30):
    newTx = Tx()
    new_pr, new_pu = generate_keys()
    indexed_input(newTx, this_pu, 0.3, pu_indices)
    newTx.add_output(new_pu, 0.3)
    newTx.sign(this_pr)
    B6.addtx(newTx)
    this_pu, this_pr = new_pu, new_pr
    savePrev = B6.previousBlock
    B6.previousBlock = None
    this_size = len(pickle.dumps(B6))
    #print("Size = " + str(this_size))
    B6.previousBlock = savePrev
    if B6.is_valid() and this_size > 10000:
        print("Error! Big blocks is valid!")
    elif (B6.is_valid) and this_size <= 10000:
        print("Error! Small blocks are invalid!")
    else:
        print("Success! Block size check passed.", str(this_size))
    pu_indices[pu4] = pu_indices[pu4] - 1
    
    overspend = Tx()
    indexed_input(overspend, pu1, 45, pu_indices)
    overspend.add_output(pu2, 44.5)
    overspend.sign(pr1)
    B7 = TxBlock(B4)
    B7.addtx(overspend)
    if B7.is_valid():
        print("Error! Overspend not detected.")
    else:
        print("Success! Overspend detected.")

    overspend1 = Tx()
    indexed_input(overspend1, pu1, 5, pu_indices)
    overspend1.add_output(pu2, 4.5)
    overspend1.sign(pr1)
    B7 = TxBlock(B4)
    B7.addtx(overspend1)
    overspend2 = Tx()
    indexed_input(overspend2, pu1, 15, pu_indices)
    overspend2.add_output(pu3, 14.5)
    overspend2.sign(pr1)
    B7 = TxBlock(B4)
    B7.addtx(overspend2)
    overspend3 = Tx()
    indexed_input(overspend3, pu1, 5, pu_indices)
    overspend3.add_output(pu4, 4.5)
    overspend3.sign(pr1)
    B7 = TxBlock(B4)
    B7.addtx(overspend3)
    overspend4 = Tx()
    indexed_input(overspend4, pu1, 8.0, pu_indices)
    overspend4.add_output(pu2, 4.5)
    overspend4.sign(pr1)
    B7 = TxBlock(B4)
    B7.addtx(overspend4)



    