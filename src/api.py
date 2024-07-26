import requests
import json
import ssl

SSL_CONTEXT                = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
SSL_CONTEXT.check_hostname = True

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
                                url     = f"{api_config['api_url']}/{proof_type}/v1/pre-login",  
                                data    = json.dumps(payload),
                                verify  = SSL_CONTEXT.check_hostname, 
                                timeout = 2
                            )
    if response.status_code != 200:
        session = None
        return None
    return response.json()["result"]["message"]


def login(session,api_config, proof_type,payload):
    response = session.post(
                                url     = f"{api_config['api_url']}/{proof_type}/v1/login",  
                                data    = json.dumps(payload),
                                verify  = SSL_CONTEXT.check_hostname, 
                                timeout = 2
                            )
    if response.status_code == 200 and response.json()["result"]["success"]:
       return response
    else: 
        logger.Error(response.Error)
        session = None
        return None

def get_provers(session,api_config, proof_type):
    response = session.post(
                                url     = f"{api_config['api_url']}/{proof_type}/v1/provers",  
                                verify  = SSL_CONTEXT.check_hostname, 
                                timeout = 2
                            )
    if response.status_code != 200:
        logger.Error(response.Error)
        session = None
        return None   
    else :
        return response.json()["result"]



def request_challenge(session,api_config, proof_type,challenge_id):
    
    def create_request_challenge_payload(challenge_id):
     return {
            "challenge_id": challenge_id
        }
    
    payload = create_request_challenge_payload(challenge_id)
    
    try:
        response = session.post(
                                url     = f"{api_config['api_url']}/{proof_type}/v1/challenge-request-dcl",  
                                data    = json.dumps(payload),
                                verify  = SSL_CONTEXT.check_hostname, 
                                timeout = 2
                            )
    except requests.exceptions.RequestException as e:
        logger.Error(f'Request failed: {e}')
        session = None
        return None
    return response.json()