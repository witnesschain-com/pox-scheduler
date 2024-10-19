import requests
import json
import ssl
import os

import logging

LOGPATH = "./"
LOGNAME = LOGPATH+"pox_schedule.log"
# Configure the logging
logging.basicConfig(filename=LOGNAME,
                    filemode='a',
                    level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

full_path = os.path.abspath(__file__)
SRC_PATH=os.path.dirname(full_path)+"/"


SSL_CONTEXT                = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
SSL_CONTEXT.check_hostname = True

TIMEOUT_SECS = 120

def create_pre_login_payload(ethereum_address, proof_config, account_config, proof_type):
     return {
            "publicKey": ethereum_address,
            "proof_type": proof_type,
            "walletPublicKey": {
                "ethereum": ethereum_address
            },
            "keyType": account_config["key_type"],
            "role":proof_config["role"],
            "projectName": proof_config["project_name"],
            "claims": {	
                        "bandwidth" : 10
                    }
        }


def get_pre_login_message(session, api_config, proof_type, payload):
    response = session.post(
                                url     = f"{api_config['api_url']}/{proof_type}/pre-login",  
                                data    = json.dumps(payload),
                                verify  = SSL_CONTEXT.check_hostname, 
                                timeout = TIMEOUT_SECS
                            )
    if response.status_code != 200:
        session = None
        return None
    return response.json()["result"]["message"]


def login(session,api_config, proof_type,payload):
    response = session.post(
                                url     = f"{api_config['api_url']}/{proof_type}/login",  
                                data    = json.dumps(payload),
                                verify  = SSL_CONTEXT.check_hostname, 
                                timeout = TIMEOUT_SECS
                            )
    if response.status_code == 200 and response.json()["result"]["success"]:
       return response
    else: 
        logger.error(response)
        session = None
        return None

def get_provers(session,api_config, proof_type):
    response = session.post(
                                url     = f"{api_config['api_url']}/{proof_type}/provers",  
                                verify  = SSL_CONTEXT.check_hostname, 
                                timeout = TIMEOUT_SECS
                            )
    if response.status_code != 200:
        logger.error(response)
        session = None
        return None   
    else :
        return response.json()["result"]


def get_user_info(session,api_config, proof_type):
    response = session.post(
                                url     = f"{api_config['api_url']}/{proof_type}/user-info",
                                verify  = SSL_CONTEXT.check_hostname, 
                                timeout = TIMEOUT_SECS
                            )
    if response.status_code != 200:
        logger.error(response)
        session = None
        return None   
    else :
        return response.json()["result"]



def request_challenge(session,api_config, proof_type, prover, challenge_id, challenge_type="NA"):
    
    def create_request_challenge_payload():
        if proof_type == "pob":
            return {
                    "challenge_id": challenge_id,
                    "prover": prover,
                    "challenge_type": challenge_type
                }
        elif proof_type == "pol":
            return {
                    "challenge_id": challenge_id,
                    "prover": prover
                }
        else:
            return Exception("Invalid Proof type")
    
    payload = create_request_challenge_payload()
    
    try:
        response = session.post(
                                url     = f"{api_config['api_url']}/{proof_type}/challenge-request-dcl",  
                                data    = json.dumps(payload),
                                verify  = SSL_CONTEXT.check_hostname, 
                                timeout = TIMEOUT_SECS
                            )
        if response.status_code != 200:
            logger.error(f'Request failed: {response.reason}')
            session = None
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f'Request failed: {e}')
        session = None
        return None
    return response.json()


def get_statistics(session,api_config, proof_type):
    response = session.post(
                                url     = f"{api_config['api_url']}/{proof_type}/statistics",
                                verify  = SSL_CONTEXT.check_hostname, 
                                timeout = TIMEOUT_SECS
                            )
    if response.status_code != 200:
        logger.error(response)
        session = None
        return None   
    else :
        return response.json()["result"]

def get_provers(session,api_config, proof_type):
    response = session.post(
                                url     = f"{api_config['api_url']}/{proof_type}/provers",
                                verify  = SSL_CONTEXT.check_hostname, 
                                timeout = TIMEOUT_SECS
                            )
    if response.status_code != 200:
        logger.error(response)
        session = None
        return None   
    else :
        return response.json()["result"]