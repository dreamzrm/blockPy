from ipaddress import ip_address
import socket 
import pickle
import select

TCP_PORT = 5005
BUFFER_SIZE = 1024
ip='127.0.0.1'


def newServerConnection(port):
    global ip
    ip='127.0.0.1'
    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ip, port))
    s.listen(5)
    return s

def recvObj(socket):
    inputs, outputs, errs =select.select([socket], [], [socket], 6)
    if socket in inputs:
     new_sock, addr=socket.accept()
     all_data =b''
     while True:
        data = new_sock.recv(BUFFER_SIZE)
        if not data: break
        all_data = all_data + data
     return pickle.loads(all_data)
    return None

def sendObj(inObj, port=TCP_PORT):
    s= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, port))
    data = pickle.dumps(inObj)
    s.send(data)
    s.close()
    return False

if __name__ == "__main__":
    server = newServerConnection(5006)
    O = recvObj(server)
    print("Success!")# if returns after time , then successful
    print(O)
    server.close()




    import threading
import time
import TxBlock
import socketUtil
import Transactions
import Signatures
import miner

head_blocks = [None]
wallets = [('192.168.0.5', 5005)]
miners = [('192.168.0.5', 5005)]
break_now=False

def walletServer(my_addr):
    global head_blocks
    head_blocks = [None]
    server = socketUtil.newServerConnection(5006)
    while not break_now:
      newBlock = socketUtil.recvObj(server)
      if isinstance(newBlock, TxBlock.TxBlock):
        print("Rec'd block")
        for b in head_blocks:
          if b == None:
            if newBlock.previousHash == None:
              newBlock.previusBlock = b
              if not newBlock.is_valid():
                  print("Error! newBlock is not valid")
              else:
               head_blocks.remove(b)
               head_blocks.append(newBlock)
               print("Added to head blocks\n")
          elif newBlock.previousHash == b.computeHash():
            newBlock.previusBlock = b
            if not newBlock.is_valid():
                  print("Error! newBlock is not valid")
            else:
             head_blocks.remove(b)
             head_blocks.append(newBlock)
             print("Added to head blocks\n")
        #What if I add to an earlier (non-head) block
    server.close()
    return True

def getBalance(pu_key):
    long_chain = TxBlock.findLongestBlockchain(head_blocks)
    this_block = long_chain
    bal = 0.0
    while this_block != None:
        for tx in this_block.data:
            for addr, amt in tx.inputs:
                if addr == pu_key:
                    bal=bal-amt
            for addr, amt in tx.outputs:
                if addr == pu_key:
                    bal=bal+amt
        this_block = this_block.previousBlock
    return 0.0

def sendCoins(pu_send, amt_send, pr_send, pu_recv, amt_recv, miner_list):
    newTx = Transactions.Tx()
    newTx.add_input(pu_send, amt_send)
    newTx.add_output(pu_recv, amt_recv)
    newTx.sign(pr_send)
    socketUtil.sendObj(newTx, 5006)
    return True

if __name__=="__main__":
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
 sendCoins(pu1, 1.0, pr1, pu2, 1.0, miners)
 sendCoins(pu1, 1.0, pr1, pu3, 0.3, miners)

 time.sleep(3)

 #Query balance
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

 miner.break_now = True
 break_now = True

 t1.join()
 t2.join()
 t3.join()

 print("Exit successful")
