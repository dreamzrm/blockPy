import threading
from TxBlock import TxBlock
import miner
import Signatures
import time

my_ip = '127.0.0.1'

wallets=[(my_ip, 5005), (my_ip, 5006)]

my_pr, my_pu = Signatures.loadKeys("private.key", "public.key")
t1 = threading.Thread(target=miner.minerServer, args=(5007,))
t2 = threading.Thread(target=miner.nonceFinder, args=(wallets, my_pu))
t1.start()
t2.start()
time.sleep(20)
miner.stopAll()
t1.join()
t2.join()

print(ord(TxBlock.findLongestBlockchain(miner.head_blocks).previousBlock.previousBlock.nonce[0]))
print(ord(TxBlock.findLongestBlockchain(miner.head_blocks).previousBlock.nonce[0]))
print(ord(TxBlock.findLongestBlockchain(miner.head_blocks).nonce[0]))