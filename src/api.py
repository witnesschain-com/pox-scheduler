import requests
import json
import ssl
import os
from datetime import datetime, timedelta

import logging

LOGPATH = "./"
LOGNAME = LOGPATH+"pox_schedule.log"
CHALLENGE_END_STATES =  [   "ENDED_SUCCESSFULLY",
                            "ENDED_WITH_PARTIAL_SUCCESS", 
                            "ERROR_NOT_ENOUGH_CHALLENGERS",
                            "ERROR_ENDED_WITH_FAILURE"
                        ]
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
        logger.error(response.reason)
        session = None
        return None
    return response.json()["result"]["message"]


def login(session,api_config, proof_type,payload):
    try:
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
    except KeyError:
        pass
    except Exception as e:
        logger.error(e)

def get_provers(session,api_config, proof_type):
    response = session.post(
                                url     = f"{api_config['api_url']}/{proof_type}/provers",
                                data    = json.dumps(
                                    { 
                                        "skip": 0 ,
                                        "limit": 10000
                                    }
                                    ),
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
            logger.error(f'Status of challenge trigger for challenge_id: {challenge_id} - {response.text}')
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f'Request failed: {e},  {e.message}')
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

def get_challenge_status(session,api_config, proof_type, challenge_id):

    payload = {
                    "challenge_id": challenge_id
    }

    response = session.post(
                                url     = f"{api_config['api_url']}/{proof_type}/challenge-status-dcl",
                                data    = json.dumps(payload),
                                verify  = SSL_CONTEXT.check_hostname, 
                                timeout = TIMEOUT_SECS
                            )
    if response.status_code != 200:
        logger.error(response.status_code,response.reason)
        return None   
    else :
        return response.json()["result"]

def get_challenger(session,api_config, proof_type,challenger_id):
    response = session.post(
                                url     = f"{api_config['api_url']}/{proof_type}/challenger",
                                json    = { 
                                       "id": challenger_id
                                    }
                                   ,
                                verify  = SSL_CONTEXT.check_hostname, 
                                timeout = TIMEOUT_SECS
                            )
    if response.status_code != 200:
        logger.error(response.reason)
        return None
    else :
        return response.json()["result"]


def has_challenge_ended(session,api_config, proof_type,challenge_id):
    try:
        response = get_challenge_status(session, api_config, proof_type, challenge_id)
        if not response:
            return (True,"FAILED")
        current_state = response["state"]
        has_ended = current_state in CHALLENGE_END_STATES
        return has_ended, current_state
    except Exception as e:
        logger.error(e)
        return (True,"FAILED")
    
def is_alive_yet (last_alive,time_delta):
    if last_alive:
        date_obj = datetime.fromisoformat(last_alive.replace('Z', '+00:00'))
        current_time = datetime.now(date_obj.tzinfo)
        time_difference = current_time - date_obj
        return time_difference < timedelta(minutes=time_delta)
    return False