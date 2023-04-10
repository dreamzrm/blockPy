import pickle
from re import T
from typing import Any
import TxBlock
import socketUtil
import Transactions
import Signatures

head_blocks = [None]
wallets = [('127.0.0.1', 5006)]
miners = [('127.0.0.1', 5006)]
break_now = False
verbose = False
my_private, my_public = Signatures.generate_keys()
tx_index = {}


def stopAll():
    global break_now 
    break_now = True

def walletServer(my_addr):
    global head_blocks
    global tx_index
    try:
        head_blocks = [None]#TxBlock.loadBlocks("AllBlocks.dat")
    except:
        head_blocks = TxBlock.loadBlocks("Genesis.dat")
    try:
        fp=open("tx_index.dat", "rb")
        tx_index = pickle.load(fp)
        fp.close()
    except:
        tx_index={}
    server = socketUtil.newServerConnection(5005)
    while not break_now:
      newBlock = socketUtil.recvObj(server)
      if isinstance(newBlock, TxBlock.TxBlock):
        TxBlock.processNewBlock(newBlock, head_blocks);  
        print("Rec'd block")
        found = False
       
              #TODO handle orphaned blocks
        #What if I add to an earlier (non-head) block
    TxBlock.saveBlocks(head_blocks, "WalletBlocks.dat")
    server.close()
    fp=open("tx_index.dat", "wb")
    pickle.dump(tx_index, fp)
    fp.close()
    return True

def getBalance(pu_key):
    long_chain = TxBlock.findLongestBlockchain(head_blocks)
    return TxBlock.getBalance(pu_key, long_chain)
    

def sendCoins(pu_send, amt_send, pr_send, pu_recv, amt_recv, inx_override=tx_index):
    global tx_index
    newTx = Transactions.Tx()
    if not pu_send in tx_index:
        tx_index[pu_send]=0
    newTx.add_input(pu_send, amt_send, tx_index[pu_send])
    newTx.add_output(pu_recv, amt_recv)
    newTx.sign(pr_send)
    for ip, port in miners:
     socketUtil.sendObj(newTx, port)
    tx_index[pu_send] = tx_index[pu_send] + 1
    return True

def loadKeys(pr_file, pu_file):
    return Signatures.loadPrivate(pr_file), Signatures.loadPublic(pu_file)


if __name__=="__main__":
 import threading
 import time
 import miner
 import Signatures
 def Thief(my_port):
    my_ip = '192.168.0.4'
    server = socketUtil.newServerConnection(my_port)
    # Get txs fron wallets
    while not break_now:
        newTx = socketUtil.recvObj(server)
        if isinstance(newTx, Transactions.Tx):
           for ip, port in miners:
                if not ip==my_ip and port == my_port:
                   socketUtil.sendObj(newTx, my_port)
 miner_pr, miner_pu = Signatures.generate_keys()
 t1 = threading.Thread(target=miner.minerServer, args=(5005,))
 t2 = threading.Thread(target=miner.nonceFinder, args=(wallets, miner_pu))
 t3 = threading.Thread(target=walletServer, args=(5006,))
 t1.start()
 t2.start()
 t3.start()

 pr1, pu1 = Signatures.generate_keys()
 pr2, pu2 = Signatures.generate_keys()
 pr3, pu3 = Signatures.generate_keys()

 #Query balances
 bal1 = getBalance(pu1)
 print("Balance 1 = "+str(bal1))
 bal2 = getBalance(pu2)
 bal3 = getBalance(pu3)

 #Send coins
 sendCoins(pu1, 0.1, pr1, pu2, 0.1)
 sendCoins(pu1, 0.1, pr1, pu2, 0.1)
 sendCoins(pu1, 0.1, pr1, pu2, 0.1)
 sendCoins(pu1, 0.1, pr1, pu2, 0.1)
 sendCoins(pu1, 0.1, pr1, pu2, 0.1)
 sendCoins(pu1, 0.1, pr1, pu2, 0.1)
 sendCoins(pu1, 0.1, pr1, pu2, 0.1)
 sendCoins(pu1, 0.1, pr1, pu2, 0.1)
 sendCoins(pu1, 0.1, pr1, pu2, 0.1)
 sendCoins(pu1, 0.1, pr1, pu2, 0.1)
 sendCoins(pu1, 0.01, pr1, pu3, 0.03)
 sendCoins(pu1, 0.01, pr1, pu3, 0.03)
 sendCoins(pu1, 0.01, pr1, pu3, 0.03)
 sendCoins(pu1, 0.01, pr1, pu3, 0.03)
 sendCoins(pu1, 0.01, pr1, pu3, 0.03)
 sendCoins(pu1, 0.01, pr1, pu3, 0.03)
 sendCoins(pu1, 0.01, pr1, pu3, 0.03)
 sendCoins(pu1, 0.01, pr1, pu3, 0.03)
 sendCoins(pu1, 0.01, pr1, pu3, 0.03)
 sendCoins(pu1, 0.01, pr1, pu3, 0.03)


 time.sleep(15)

 #Save/load all blocks
 TxBlock.saveBlocks(head_blocks, "AllBlocks.dat")
 head_blocks = TxBlock.loadBlocks("AllBlocks.dat")

 #Query balances
 new1 = getBalance(pu1)
 print("Balance 1 = "+str(new1))
 new2 = getBalance(pu2)
 new3= getBalance(pu3)

 #Verify balances
 if abs(new1-bal1+2.0)>0.0000000001:
     print("Error! Wrong balance for pu1")
 else:
     print("Success! Good balance for pu1")
 if abs(new2-bal2-1.0)>0.0000000001:
     print("Error! Wrong balance for pu2")
 else:
     print("Success! Good balance for pu2")
 if abs(new3-bal3-0.3)>0.0000000001:
     print("Error! Wrong balance for pu3")
 else:
     print("Success! Good balance for pu3")

 #Thief will try to duplicate transactions
 miner.append(('192.168.0.4', 5007))
 t4 = threading.Thread(target=Thief, args=(5007,))
 t4.start()
 sendCoins(pu2, 0.2, pr2, pu1, 0.2)
 time.sleep(20)
 #Check balances
 newnew1 = getBalance(pu1)
 print(newnew1)
 if (abs(newnew1 - new1 - 0.2)> 0.0000001):
     print("Error! Duplicate Txs accepted.")
 else:
     print("Success! Duplicate Txs rejected.")

 miner.stopAll()

 num_heads = len(head_blocks)
 sister = TxBlock.TxBlock(head_blocks[0].previousBlock.previousBlock)
 sister.previousBlock = None
 socketUtil.sendObj(sister, 5006)

 time.sleep(10)
 if(len(head_blocks)==num_heads +1):
     print("Success! New head_block created")
 else:
     print("Error! Failed to add sister block")

 stopAll()

 t1.join()
 t2.join()
 t3.join()

 print("Exit successful")
