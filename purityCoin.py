import threading
import Signatures
from TxBlock import TxBlock
import miner
import time
import wallet

wallets=[]
miners=[]
my_ip= '127.0.0.1'
wallets.append((my_ip, 5006))
wallets.append((my_ip, 5007))
miners.append((my_ip, 5005))

tMS = None
tNF = None
tWS = None

def startMiner():
    global tMS, tNF
    try:
        my_pu = Signatures.loadPublic("public.key")
    except:
        pass #TODO
    tMS = threading.Thread(target=miner.minerServer, args=(5005,))
    tNF = threading.Thread(target=miner.nonceFinder, args=(wallets, my_pu))
    tMS.start()
    tNF.start()
    #Start nonceFinder
    #Start minerServer
    #Load tx_list
    #Load head_blocks
    #Load public_key
    return True
def startWallet():
    global tWS
    wallet.my_private, wallet.my_public = wallet.loadKeys("private.key", "public.key")
    tWS = threading.Thread(target=wallet.walletServer, args=(5006, ))
    tWS.start()
    #Start walletServer
    #Load public and private keys
    #Load head_blocks
    return True

def stopMiner():
    global tMS, tNF
    miner.stopAll()
    if tMS: tMS.join()
    if tNF: tNF.join()
    #Stop nonceFinder
    #Stop minerServer
    #Save tx_list
    #Save head_blocks
    return True
def stopWallet():
    global tWS
    wallet.stopAll()
    if tWS: tWS.join()
    #Stop walletServer
    #Save head_blocks
    return True

def getBalance(pu_key):
    if not tWS:
        print("Start the server by calling startWallet before checking balances")
        return 0.0
    return wallet.getBalance(pu_key)

def sendCoins(pu_recv, amt, tx_fee):
    wallet.sendCoins(wallet.my_public, amt+tx_fee, wallet.my_private, pu_recv, amt, miners)
    return True



if __name__ == "__main__":
   startMiner()
   startWallet()
   other_public = b'-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEApcX2zta0P31NNGEskp4p\nyowaOO76jrHQGCiWgsN42ns42aWqx4LXxoKGOIZ5X+SNd3cjdyPvPEeibcY5XFmm\n/miayt3n0Sl4Zdgp75FpbP6yy7ipzz5kTKP+1ScxkzQAID2E9EuADEdikjEfh0i9\n1qTSSP5WVxrF5HHIW+0WQPcVeYOhx//bp8oGRdRHcAE/d7ckOrb7jeRVFRqqxLwo\nHR4TTaYzC5Pczm5rWa7EPgidG1oSD1cVQoXSanxIelEQj159uFrRQ/qxu505NhLn\nstGzskXV8ZGaphP8YKygdhBUYqj/FGc5Jg/qYEXVWCP0elR+hYXuQ8XTcRUq9WRz\newIDAQAB\n-----END PUBLIC KEY-----\n'
   time.sleep(2)
   print(getBalance(wallet.my_public))
   sendCoins(other_public, 1.0, 0.001)
   time.sleep(4)
   print(getBalance(other_public))
   print(getBalance(wallet.my_public))

   time.sleep(10)
   stopWallet()
   stopMiner()

   print(ord(TxBlock.findLongestBlockchain(miner.head_blocks).previousBlock.previousBlock.nonce[0]))
   print(ord(TxBlock.findLongestBlockchain(miner.head_blocks).previousBlock.nonce[0]))
   print(ord(TxBlock.findLongestBlockchain(miner.head_blocks).nonce[0]))  