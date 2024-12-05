from   web3                 import Web3, exceptions  
from   eth_account          import Account
from   eth_utils            import to_bytes
from   eth_account.messages import encode_defunct
import eth_abi

import os
import sys
import json


def get_web3_account(private_key):
    return Account.from_key(private_key)


def connect_to_rpc(rpc_url):
    connection_rpc = Web3(Web3.HTTPProvider(rpc_url))

    if connection_rpc.is_connected():
        return connection_rpc
    else:
        print("Failed to connect to Chain. Check your RPC URL.")
        return None

def sign_message(message,account):
    encoded_message = encode_defunct(text=message)
    signed_message = account.sign_message(encoded_message)
    return signed_message

def get_contract_with_abi(connection_rpc, abi_file, contract_address):
    with open(abi_file,"r") as abi_file:
        contract_abi = json.load(abi_file)
        return connection_rpc.eth.contract(address=contract_address, abi=contract_abi)
    return None

def submit_transaction(chain_id, connection_rpc, gas_limit, caller_account, contract_address, abi_file, function_name, *params):    
    
    def get_nonce(connection_rpc,account):
        return connection_rpc.eth.get_transaction_count(account.address)

    contract = get_contract_with_abi(connection_rpc,abi_file,contract_address)
    
    nonce = get_nonce(connection_rpc,caller_account)
    contract_function = getattr(contract.functions, function_name)

    transaction = contract_function(*params).build_transaction({
      "chainId"  : chain_id, 
      "gas"      : gas_limit,  
      "gasPrice" : 0,  
      "nonce"    : nonce,
    })
    
    signed_transaction = caller_account.sign_transaction(transaction)
    transaction_receipt = connection_rpc.eth.send_raw_transaction(signed_transaction.rawTransaction)
    receipt = connection_rpc.eth.wait_for_transaction_receipt(transaction_receipt)

    return receipt,contract
    