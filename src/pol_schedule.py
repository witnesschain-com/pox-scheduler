import requests
import json
import os
import ssl
from eth_account import Account
from eth_account.messages import encode_defunct
from chain import *

import logging

#### SET PRIVATE_KEY of the payer in your environment variables

# Configure the logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# Example usage
logger = logging.getLogger(__name__)



# Endpoint related
API_URL                    = "https://api.witnesschain.com" 
CONTENT_TYPE_JSON          = {
                                "content-type" : "application/json"
                             }
SSL_CONTEXT                = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
SSL_CONTEXT.check_hostname = True


# Chain related parameters
RPC_URL                    = "https://blue-orangutan-rpc.eu-north-2.gateway.fm"
REQUEST_HANDLER_PROXY      = "0x8A02C91373929a4764F015309B072DC9C9Fabc49"
#REQUEST_HANDLER_PROXY      = "0x358Dc77948056fA1d89f6067b179F6cb3BF555fC"
CHAIN_ID                   = 1237146866
PROVER_REGISTRY_PROXY      = "0x91013d3CecE055603D8b1EE7DCB1f670f480fe24"
#PROVER_REGISTRY_PROXY      = "0x94029Ac6F6E41Cf36276E75ABb4E50D0fB2d4cF5"
GAS_LIMIT                  = 2000000
ABI_FILE_NAME              = "request_handler.abi"


# Proof related parameters
PROOF                      = "pol"
NUM_CHALLENGERS            = 1
CHALLENGERS_TOLERANCE      = 1
CHALLENGE_TIMEOUT_SECS     = 350 # Should be greater than 300
ATTRIBUTE_IDS              = ["pol02"]
ROLE                       = "payer"
PROJECT_NAME               = "WITNESS_CHAIN"


# Account related parameters
KEY_TYPE                   = "ethereum"
PAYER_PRIVATE_KEY          = os.getenv('PRIVATE_KEY')

def validate_inputs():
    assert(CHALLENGE_TIMEOUT_SECS > 300)


def create_pre_login_payload(ethereum_address):
     return {
            "publicKey": ethereum_address,
            "proof_type": PROOF,
            "walletPublicKey": {
                "ethereum": ethereum_address
            },
            "keyType": KEY_TYPE,
            "role":ROLE,
            "projectName": PROJECT_NAME,
            "claims": {	
                        "bandwidth" : 10
                    }
        }


def get_pre_login_message(session,payload):
    response = session.post(
                                url     = f"{API_URL}/{PROOF}/v1/pre-login",  
                                data    = json.dumps(payload),
                                verify  = SSL_CONTEXT.check_hostname, 
                                timeout = 2
                            )
    if response.status_code != 200:
        session = None
        return None
    return response.json()["result"]["message"]


def sign_message(message,account):
    encoded_message = encode_defunct(text=message)
    signed_message = account.sign_message(encoded_message)
    return signed_message


def login(session,payload):
    response = session.post(
                                url     = f"{API_URL}/{PROOF}/v1/login",  
                                data    = json.dumps(payload),
                                verify  = SSL_CONTEXT.check_hostname, 
                                timeout = 2
                            )
    if response.status_code == 200 and response.json()["result"]["success"]:
        cookies = session.cookies.get_dict()
        print(cookies)
        return cookies["__Secure-t"]
    return None


def get_provers(session):
    response = session.post(
                                url     = f"{API_URL}/{PROOF}/v1/provers",  
                                verify  = SSL_CONTEXT.check_hostname, 
                                timeout = 2
                            )
    if response.status_code != 200:
        session = None
        return None   
    else :
        return response.json()["result"]


def submit_on_chain_request_for_challenge(account, timeout, attribute_ids, prover, is_ip_v6, challengers_count, tolerance, latitude, longitude):
    connection_to_rpc = connect_to_rpc(RPC_URL)
    challenge_info = eth_abi.encode (
        ["address","address","bool","uint256","uint256","int256","int256"],
        [PROVER_REGISTRY_PROXY, prover,is_ip_v6,challengers_count,tolerance,latitude,longitude]
    )

    receipt,contract = submit_transaction(  
                                            CHAIN_ID, 
                                            connection_to_rpc,
                                            GAS_LIMIT,
                                            account,
                                            REQUEST_HANDLER_PROXY,
                                            ABI_FILE_NAME,
                                            "submitRequest",
                                            timeout,
                                            attribute_ids,
                                            [challenge_info]
                                        )
    logs = contract.events.RequestProcessed().process_receipt(receipt)

    request_id = 0
    new_challenges = []

    for log in logs:
        request_id     = log['args']['requestId']
        new_challenges = log['args']['newChallenges']

    return request_id, new_challenges

def create_request_challenge_payload(challenge_id):
     return {
            "challenge_id": challenge_id
        }

def request_challenge(session,challenge_id):
    payload = create_request_challenge_payload(challenge_id)
    print(payload)
    try:
        response = session.post(
                                url     = f"{API_URL}/{PROOF}/v1/challenge-request-dcl",  
                                data    = json.dumps(payload),
                                verify  = SSL_CONTEXT.check_hostname, 
                                timeout = 2
                            )
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    if response.status_code != 200:
        print (response.reason,response.text)
        session = None
        return None
    return response.json()


def main():
    validate_inputs()
    account = get_web3_account(PAYER_PRIVATE_KEY)
    with requests.Session() as session:
        session.headers.update(CONTENT_TYPE_JSON)

        pre_login_payload = create_pre_login_payload(account.address)

        # Step 1: Get pre-login message
        message = get_pre_login_message(session, pre_login_payload)
        if not message:
            print ("Error: Unable to PRE_LOGIN")
            return None 
        logger.info('Pre-login successful')


        # Step 2: Sign the message
        signed_message = sign_message(message, account)
        signed_payload = {
            "signature": signed_message.signature.hex()
        }

        # Step 3: Log in
        token = login(session, signed_payload)
        if not token:
            logger.Error('Error: Login failed')
            return None
        logger.info('Login successful')

        # Step 4: Get prover IDs
        provers = get_provers(session)
        logger.info('Got Provers')
        
        # Step 5: Request challenge for each prover
        for prover in provers["provers"]:
            print(f"\n")
            prover_id = prover["id"].split("/")[1]
            is_ip_v6 = True if prover["id"].split("/")[0] == "IPv6" else False
            latitude = int(prover["claims"]["latitude"] * 10**18)
            longitude = int(prover["claims"]["longitude"] * 10**18)
            request_id, challenges = submit_on_chain_request_for_challenge(
                                                                                account,
                                                                                CHALLENGE_TIMEOUT_SECS,
                                                                                ATTRIBUTE_IDS,
                                                                                prover_id,
                                                                                is_ip_v6,
                                                                                NUM_CHALLENGERS,
                                                                                CHALLENGERS_TOLERANCE,
                                                                                latitude,
                                                                                longitude
                                                                            )
            for challenge in challenges:
                if challenge:
                    print(request_challenge(session,challenge))


if __name__ == "__main__":
    main()
