import pickle
import time
import socketUtil
import socket
import Transactions
import TxBlock
import Signatures
import threading

localhost = '192.168.52.245'

wallets = [('192.168.52.245',5006)]
tx_list = []
head_blocks = [None]
break_now=False
verbose = True

def stopAll():
    global break_now 
    break_now = True

def findLongestBlockchain():
    longest = -1
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
def minerServer(my_port):
    global tx_list
    global break_now
    global head_blocks
    try: 
        tx_list = loadTxList("Txs.dat")
        if verbose: print("Loaded tx_list has "+str(len(tx_list))+" Txs.")
    except:
        print("No previous Txs. Starting fresh")
        tx_list=[]
    head_blocks = [None]
    # Open server
    server = socketUtil.newServerConnection(my_port)
    # Get txs fron wallets
    while not break_now:
        newObj = socketUtil.recvObj(server)
        if isinstance(newObj, Transactions.Tx):
            #TODO check transactions for goodness in nonceFinder
            #TODO check transactions for well-ordered indices
            #TODO oredr tx_list to make indices well-ordered
           duplicate = False
           for addr, amt, inx in newObj.inputs:
                   for tx in tx_list:
                       for addr2, amt2, inx2 in tx.inputs:
                          if addr2 == addr and inx2 == inx:
                                duplicate = True
           if duplicate: break
           tx_list.append(newObj)
           if verbose : print("Recd tx")
        elif isinstance(newObj, TxBlock.TxBlock):
            print("Rec'd new block")
            TxBlock.processNewBlock(newObj, head_blocks, True)
            for tx in newObj.data:
                if tx in tx_list:
                    tx_list.remove(tx)
        else:
            print("Rec'd" + str(type(newObj)))
    if verbose: print("Saving "+ str(len(tx_list))+" txs to Txs.dat")       
    saveTxList(tx_list, "Txs.dat")
    return False

def nonceFinder(wallet_list, miner_public):
    global break_now
    global head_blocks
    try:
        head_blocks = [None]#TxBlock.loadBlocks("AllBlocks.dat")
    except:
        print("No previous blocks found. Starting fresh")
        head_blocks = TxBlock.loadBlocks("Genesis.dat")
    #Add Txs to new block
    while not break_now:
     newBlock = TxBlock.TxBlock(TxBlock.findLongestBlockchain(head_blocks))
     placeholder = Transactions.Tx()
     placeholder.add_output(miner_public, 25.0)
     newBlock.addtx(placeholder)
     #TODO sort tx_list by tx fee per byte
     for tx in tx_list:
      newBlock.addtx(tx)
      if not newBlock.check_size():
          newBlock.removeTx(tx)
          break
     newBlock.removeTx(placeholder)
     if verbose: print("new block has "+str(len(newBlock.data))+" txs")
    # Compute and add mining reward
     total_in, total_out = newBlock.count__totals()
     mine_reward = Transactions.Tx()
     mine_reward.add_output(miner_public, 25.0+total_in-total_out)
     newBlock.addtx(mine_reward)
    #Find the nonce
     if verbose: print("Finding nonce")
     newBlock.find_nonce(10000)
     if newBlock.good_nonce():
        if verbose: print("Good nonce found")
        if not newBlock.previousBlock in head_blocks:
            break
        head_blocks.remove(newBlock.previousBlock)
        head_blocks.append(newBlock)
    # Send new block
        savePrev = newBlock.previousBlock
        newBlock.previousBlock = None
        for ip_addr, port in wallet_list:
            print("Sending to "+ ip_addr+":"+str(port))
            socketUtil.sendObj(newBlock, port)
        newBlock.previousBlock = savePrev
    # Remove used txs from tx_list
        for tx in newBlock.data:
            if tx != mine_reward:
                tx_list.remove(tx)
    #open server connection
    #rec'v 2 transactions
    #collect into block
    #find nonce
    #send that block to each in wallet_list
    TxBlock.saveBlock(head_blocks, "AllBlocks.dat")
    return True

def loadTxList(filename):
    fin = open(filename, "rb")
    oF = pickle.load(fin)
    fin.close()
    return oF

def saveTxList(the_list, filename):
    fs = open(filename, "wb")
    pickle.dump(the_list, fs)
    fs.close()
    return True

if __name__=="__main__":
 
 import time
 my_pr, my_pu = Signatures.generate_keys()#Signatures.loadKeys("private.key", "public.key")
 t1 = threading.Thread(target=minerServer, args=(5005,))
 t2 = threading.Thread(target=nonceFinder, args=(wallets, my_pu))
 server = socketUtil.newServerConnection(5006)
 t1.start()
 t2.start()
 pr1, pu1 = Signatures.generate_keys()
 pr2, pu2 = Signatures.generate_keys()
 pr3, pu3 = Signatures.generate_keys()
 Tx1 = Transactions.Tx()
 Tx2 = Transactions.Tx()

 Tx1.add_input(pu1, 4.0)
 Tx1.add_input(pu2, 1.0)
 Tx1.add_output(pu3, 4.8)
 Tx2.add_input(pu3, 4.0)
 Tx2.add_output(pu2, 4.0)
 Tx2.add_reqd(pu1)
 Tx1.sign(pr1)
 Tx1.sign(pr2)
 Tx2.sign(pr3)
 Tx2.sign(pr1)
 new_tx_list = [Tx1, Tx2]
 saveTxList(new_tx_list, "Txs.dat")
 new_new_tx_list = loadTxList("Txs.dat")


 for tx in new_new_tx_list:

  try:
   socketUtil.sendObj(tx)
   print("Sent Tx")
  except:
    print("Error! Connection unsuccessful")
  
 for i in range(10):
    newBlock = socketUtil.recvObj(server)
    if newBlock:
        break

 if not newBlock == None:
  if newBlock.is_valid():
    print("Success! Block is valid")
  if newBlock.good_nonce():
    print("Success! Nonce is valid")
  for tx in newBlock.data:
     try:
       if tx.inputs[0][0] == pu1 and tx.inputs[0][1] == 4.0:
         print("Tx1 is present")
     except:
         pass
     try:
       if tx.inputs[0][0] == pu3 and tx.inputs[0][1] == 4.0:
         print("Tx2 is present")
     except:
         pass
     time.sleep(2)
     break_now = True
     time.sleep(2)
     server.close()

 for b in head_blocks:
    if b:
     if newBlock.previousHash == b.computeHash():
        newBlock.previusBlock = b
        head_blocks.remove(b)
        head_blocks.append(newBlock)
 t1.join()
 t2.join()
 print("Done!")
