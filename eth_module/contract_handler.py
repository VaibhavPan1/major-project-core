
from web3 import Web3
import json

class ContractHandler:
    def __init__(self, ganacheurl = "HTTP://127.0.0.1:7545", account_address=None, contract_path=None):
        self.web3 = Web3(Web3.HTTPProvider(ganacheurl))
        if self.web3.is_connected():
            print("Connected to ganache")
        """
        TODO: remove default account and accept account from user(completed)
        """
        self.account_address = account_address if account_address else self.web3.eth.accounts[0]
        self.contract_path = contract_path


    def store_file_hash(self, file_name, cid, abi, contract_address):
        contract = self.web3.eth.contract(address=contract_address, abi=abi)

        tx_hash = contract.functions.storeFile(file_name, cid).transact({'from':self.account_address})
        tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"File hash stored in contract. Transaction confirmed. Transaction Hash = {self.web3.to_hex(tx_hash)}")

    def retrieve_file_hash(self, file_name, abi, contract_address):
        contract = self.web3.eth.contract(address=contract_address, abi=abi)
        cid = contract.functions.getFileHash(file_name).call()
        return cid