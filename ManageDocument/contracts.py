import sys
import time
import pprint

from web3.providers.eth_tester import EthereumTesterProvider
from web3 import Web3
from eth_tester import PyEVMBackend
from solcx import compile_source
import uuid

import models

def compile_source_file(file_path):
   with open(file_path, 'r') as f:
      source = f.read()

   return compile_source(source)


def deploy_contract(w3, abi, bytecode):
    tx_hash = w3.eth.contract(
        abi=abi,
        bytecode=bytecode).constructor().transact()

    address = w3.eth.get_transaction_receipt(tx_hash)['contractAddress']
    return address

def build(documentCreatedAction, userIDDocumentNumber):
    w3 = Web3(Web3.HTTPProvider("https://ropsten.infura.io/v3/016bdc4c4f90406bb7fd7bf77dc9fba3"))

    contract_source_path = 'contracts/iris.sol'
    compiled_sol = compile_source_file('contracts/iris.sol')

    contract_id, contract_interface = compiled_sol.popitem()

    with open('abi.txt', 'r') as file:
        thisABI = file.read().replace('\n', '')

    with open('bytecode.txt', 'r') as file:
        thisBytecode = file.read().replace('\n', '')

    address = deploy_contract(w3, thisABI, thisBytecode)
    print(f'Deployed {contract_id} to: {address}\n')
    documentBlock = models.DocumentBlock(blockAddress = address, userIDNonce = userIDDocumentNumber)
    documentBlock.save()

    iris_contract = w3.eth.contract(address=address, abi=thisABI)

    documentCreatedFingerprint = uuid.uuid4()
    iris_contract.functions.CreateDocument(documentCreatedAction, documentCreatedFingerprint)

    gas_estimate = iris_contract.functions.setVar(255).estimateGas()
    print(f'Gas estimate to transact with setVar: {gas_estimate}')

    if gas_estimate < 100000:
        print("Sending transaction to setVar(255)\n")
        tx_hash = iris_contract.functions.setVar(255).transact()
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print("Transaction receipt mined:")
        pprint.pprint(dict(receipt))
        print("\nWas transaction successful?")
        pprint.pprint(receipt["status"])
    else:
        print("Gas cost exceeds 100000")