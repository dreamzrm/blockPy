import threading
import time
import random

def printA():
    for i in range(6): 
       print("A"+str(i)+"... . ...")
       time.sleep(random.randint(1,4)*0.1)
    return 89

def printB():
    for i in range(6):  
       print("B"+str(i)+"****")
       time.sleep(random.randint(1,4)*0.1)
    return 89

def printAny(inlist):
    for item in inlist:
       print(str(item))
       time.sleep(random.randint(1,4)*0.1)


t1= threading.Thread(target=printA)

intup=(789, "Hello", [1,2,3])
t2 = threading.Thread(target=printAny, args=(intup,))

t1.start()
t2.start()

printB()

t1.join()
t2.join()

print("End here")