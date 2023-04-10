#Signatures.py
from email import utils
from hmac import digest
import pickle
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

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
        chosen_hash = hashes.SHA256()
        hasher = hashes.Hash(chosen_hash)
        hasher.update(message)
        digest = chosen_hash.finalize()
        public.verify(
            sig,
            message,
            padding.PSS(
              mgf=padding.MGF1(hashes.SHA256()),
              salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()#utils.Prehashed(chosen_hash)
        )
        return True
    except InvalidSignature:
        return False
    except:
        print("Error executing verify")
        return False
    
def savePrivate(pr_key, filename):
   pem = pr_key.private_bytes(
   encoding=serialization.Encoding.PEM,
   format=serialization.PrivateFormat.TraditionalOpenSSL,
   encryption_algorithm=serialization.NoEncryption()
   )
   fp = open(filename, "wb")
   fp.write(pem)
   fp.close()
   return True
def loadPrivate(filename):
    fin = open(filename, "rb")
    pr_key = serialization.load_pem_private_key(
        fin.read(),
        password=None,
    )
    fin.close()
    return pr_key
def savePublic(pu_key, filename):
    fp = open(filename, "wb")
    fp.write(pu_key)
    fp.close()
    return True
def loadPublic(filename):
    fin = open(filename, "rb")
    pu_key = fin.read()
    fin.close()
    return pu_key

def loadKeys(pr_file, pu_file):
    return loadPrivate(pr_file), loadPublic(pu_file)

if __name__ == '__main__':
    pr,pu = generate_keys()
    print(pr)
    print(pu)
    message = "This is a secret message"
    sig = sign(message, pr)
    print(sig)
    correct = verify(message, sig, pu)
    print(correct)

    if correct:
        print("Success! Good sig")
    else:
        print ("ERROR! Signature is bad")

    pr2, pu2 = generate_keys()

    sig2 = sign(message, pr2)

    correct= verify(message, sig2, pu)
    if correct:
        print("ERROR! Bad signature checks out!")
    else:
        print("Success! Bad sig detected")

    badmess = message + "Q"
    correct= verify(badmess, sig, pu)
    if correct:
        print("ERROR! Tampered message checks out!")
    else:
        print("Success! Tampering detected")

    savePrivate(pr2, "private.key")
    pr_load = loadPrivate("private.key")
    sig3 = sign(message, pr_load)
    correct = verify(message, sig3, pu2)
    if correct:
        print("Success! Good loaded private key!")
    else:
        print("Error! Loaded private key is bad")

    savePublic(pu2, "public.key")
    pu_load = loadPublic("public.key")

    correct = verify(message, sig3, pu_load)

    if correct:
        print("Success! Good loaded public key!")
    else:
        print("Error! Loaded public key is bad")
    