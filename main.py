from ipfs_module.ipfs_handler import IPFSHandler
from eth_module.contract_handler import ContractHandler
from db_module.db_handler import DBHandler
# from encryption.enc_handler import CryptoVault
import json
import base64
from dotenv import load_dotenv
import os
load_dotenv()

import os
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes




class CryptoVault:
    def __init__(self):
        pass

    # RSA Key Generation (for Judge and Lawyer)
    def generate_rsa_key_pair(self):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return private_pem, public_pem

    # Encrypt File for Multiple Recipients
    def encrypt_file(self, file_path, recipient_public_keys: dict):
        aes_key = os.urandom(32)  # AES-256 key
        iv = os.urandom(16)       # AES IV

        # Read file
        with open(file_path, 'rb') as f:
            plaintext = f.read()

        # Pad plaintext
        padding_len = 16 - (len(plaintext) % 16)
        padded_plaintext = plaintext + bytes([padding_len] * padding_len)

        # Encrypt file with AES
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()

        # Encrypt AES key for each recipient
        encrypted_keys = {}
        for user_id, pub_pem in recipient_public_keys.items():
            public_key = serialization.load_pem_public_key(pub_pem)
            encrypted_key = public_key.encrypt(
                aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            encrypted_keys[user_id] = encrypted_key

        return ciphertext, iv, encrypted_keys

    # Decrypt file using private key and encrypted AES key
    def decrypt_file(self, ciphertext, iv, encrypted_key, private_key_pem):
        private_key = serialization.load_pem_private_key(private_key_pem, password=None)

        # Decrypt AES key
        aes_key = private_key.decrypt(
            encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # Decrypt file
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        # Unpad
        padding_len = padded_plaintext[-1]
        plaintext = padded_plaintext[:-padding_len]

        return plaintext

#create config.json file in config folder before running this file
with open('config/config.json', 'r') as config_file:
    config = json.load(config_file)

ipfs_handler = IPFSHandler()
db_handler = DBHandler(**config['mysql'])
contract_handler = ContractHandler() #leave it blank for default account on ganache
enc_handler = CryptoVault() #leave it blank for default account on ganache


#(compile, deploy, migrate your contract using truffle, copy it's abi and contract_address from build file)
#WARNING: DON'T USE THIS ABI AND CONTRACT ADDRESS OR BYTECODE, DEPLOY YOUR OWN CONTRACT ON GANACHE USING TURUFFLE)
# abi = [
#     {
#         "inputs": [
#             {
#                 "internalType": "string",
#                 "name": "fileName",
#                 "type": "string"
#             },
#             {
#                 "internalType": "string",
#                 "name": "fileHash",
#                 "type": "string"
#             }
#         ],
#         "name": "storeFile",
#         "outputs": [],
#         "stateMutability": "nonpayable",
#         "type": "function"
#     },
#     {
#         "inputs": [
#             {
#                 "internalType": "string",
#                 "name": "fileName",
#                 "type": "string"
#             }
#         ],
#         "name": "getFileHash",
#         "outputs": [
#             {
#                 "internalType": "string",
#                 "name": "",
#                 "type": "string"
#             }
#         ],
#         "stateMutability": "view",
#         "type": "function"
#     },
#     {
#         "inputs": [
#             {
#                 "internalType": "string",
#                 "name": "",
#                 "type": "string"
#             }
#         ],
#         "name": "fileHashes",
#         "outputs": [
#             {
#                 "internalType": "string",
#                 "name": "",
#                 "type": "string"
#             }
#         ],
#         "stateMutability": "view",
#         "type": "function"
#     }
# ]
# contract_address = "0xb2100aDf3B5b8c48D2224f0B23095e8c58933E37"
contract_address = os.getenv("CONTRACT_ADDRESS")
abi = os.getenv("ABI")

def upload_file(file_path):
    file_name = file_path.split('/')[-1]
    db_cid = db_handler.retrieve_file(file_name)
    if db_cid is not None: #if file with same name exists in db, choose to replace or abort
        print(f"File name with {file_name} already exists. Do you wish to replace file?")
        option = input("Press Y to continue, press any key to abort..")
        if option == "Y" or option == "y":
            cid = ipfs_handler.upload_file(file_path)
            print(f"File uploaded to IPFS, CID: {cid}")

            #storing details in database
            db_handler.store_dublicate(file_name,cid)
            print(f"File stored in MySQL: {file_name} -> {cid}")

            #storing detalis on ethreum
            contract_handler.store_file_hash(file_name, cid, abi, contract_address)
            print("file hash stored on ethreum")

        else:
            print("Operation aborted...")
    else:
        cid = ipfs_handler.upload_file(file_path)
        print(f"File uploaded to IPFS, CID: {cid}")

        #storing details in database
        db_handler.store_file(file_name,cid)
        print(f"File stored in MySQL: {file_name} -> {cid}")

        #storing detalis on ethreum
        contract_handler.store_file_hash(file_name, cid, abi, contract_address)
        print("file hash stored on ethreum")
    return cid
    

def retrieve_file(file_name, output_path):
    cid = db_handler.retrieve_file(file_name)
    # print(f"CID retrieved from mySql: {cid}")

    cid2 = contract_handler.retrieve_file_hash(file_name=file_name, abi=abi, contract_address= contract_address)
    print(f"CID from Database = {cid}\nCID from Smart Contract = {cid2}")

    #match cid from smartcontract and database
    if (cid and cid2) and (cid == cid2):
        ipfs_handler.get_file(cid, output_path)
    else:
        print("file not found in mysql")

if __name__ == '__main__':

    judge_private, judge_public = enc_handler.generate_rsa_key_pair()
    print(judge_private, judge_public )
    lawyer_private, lawyer_public = enc_handler.generate_rsa_key_pair()
    print(lawyer_private, lawyer_public)

    file_path = 'evidence.txt'
    recipients = {
        "judge": judge_public,
        "lawyer": lawyer_public
    }

    ciphertext, iv, encrypted_keys = enc_handler.encrypt_file(file_path, recipients)
    print("Ciphertext:", ciphertext, "\nIV:", iv, "\nEncrypted Keys:", encrypted_keys)
    b64_iv = base64.b64encode(iv).decode()
    b64_key_judge = base64.b64encode(encrypted_keys['judge']).decode()
    b64_key_lawyer = base64.b64encode(encrypted_keys['lawyer']).decode()
    # print("Base64 IV:", b64_iv, "\nBase64 Encrypted Key (Judge):", b64_key_judge, "\nBase64 Encrypted Key (Lawyer):", b64_key_lawyer)

    with open ('encrypted_file2.bin', 'wb') as f:
        f.write(ciphertext)

    
    
    # it is possible to upload a directory or a file but uploading a directory is preferred
    cid = upload_file('encrypted_file2.bin') 

    retrieve_file('encrypted_file2.bin', 'download/')

    with open(f"download/{cid}", "rb") as f:
        ciphertext = f.read()
    print("Ciphertext:", ciphertext)
    
    decrypted = enc_handler.decrypt_file(ciphertext, iv, encrypted_keys["judge"], judge_private)

    with open("decrypted_evidence.txt", "wb") as f:
        f.write(decrypted)


"""
KNOWN ISSUES: 
1. Contract deployment using python is pending. Temporary fix: compiled and deployed on Ganache using Truffle.
2. IPFS version
3. Removing previous file details from database and pointing it to newer CID


"""