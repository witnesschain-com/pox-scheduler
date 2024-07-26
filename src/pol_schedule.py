#### SET PRIVATE_KEY of the payer in your environment variables

import os

from chain import *
from config.config import Config
from api import * 
from proof_validations import *

import logging

# Configure the logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# Example usage
logger = logging.getLogger(__name__)

CONFIG_FILE                = "config/config.json"
NUM_CHALLENGERS            = 10
CHALLENGERS_TOLERANCE      = 0
PAYER_PRIVATE_KEY          = os.getenv('PRIVATE_KEY')


def submit_on_chain_request_for_challenge(
                                          account, 
                                          chain_config, 
                                          proof_config, 
                                          prover, 
                                          is_ip_v6, 
                                          challengers_count, 
                                          tolerance, 
                                          latitude, 
                                          longitude
                                        ):
    
    connection_to_rpc = connect_to_rpc(chain_config["rpc_url"])

    if not connection_to_rpc:
        logger.error(f"Unable to connect to {chain_config['rpc_url']}")

    challenge_info = eth_abi.encode (
        ["address","address","bool","uint256","uint256","int256","int256"],
        [
            chain_config["prover_registry"]["proxy"], 
            prover,
            is_ip_v6,
            challengers_count if challengers_count else proof_config["number_challengers_default"],
            tolerance if tolerance else proof_config["challengers_tolerance_default"],
            latitude,
            longitude
        ]
    )

    receipt,contract = submit_transaction(  
                                            chain_config["chain_id"], 
                                            connection_to_rpc,
                                            chain_config["gas_limit"],
                                            account,
                                            chain_config["request_handler"]["proxy"],
                                            chain_config["request_handler"]["abi_file_name_with_path"],
                                            "submitRequest",
                                            proof_config["challenge_timeout_secs_minimum_default"],
                                            proof_config["attribute_ids"],
                                            [challenge_info]
                                        )
    logs = contract.events.RequestProcessed().process_receipt(receipt)

    request_id = 0
    new_challenges = []

    for log in logs:
        request_id     = log['args']['requestId']
        new_challenges = log['args']['newChallenges']

    return request_id, new_challenges


def main():

    proof_type = "pol"

    config = Config(CONFIG_FILE)
        
    api_config = config.get_api_config()
    chain_config = config.get_chain_config()
    proof_config = config.get_proof_config(proof_type)
    account_config = config.get_account_config()

    validate_inputs(proof_config)
    
    account = get_web3_account(PAYER_PRIVATE_KEY)
    
    with requests.Session() as session:
        session.headers.update(api_config["content_type_json"])

        # Step 1: Get pre-login message
        pre_login_payload = create_pre_login_payload(account.address,proof_config,account_config,proof_type)
        message = get_pre_login_message(session, api_config, proof_type, pre_login_payload)
        if not message:
            logger.error('Pre-login successful')
            return None 
        logger.info('Pre-login successful')


        # Step 2: Sign the message
        signed_message = sign_message(message, account)
        signed_payload = {
            "signature": signed_message.signature.hex()
        }

        # Step 3: Log in
        token = login(session, api_config, proof_type, signed_payload)
        if not token:
            logger.error('Error: Login failed')
            return None
        logger.info('Login successful')

        # Step 4: Get provers
        provers = get_provers(session, api_config, proof_type)
        if not provers:
            logger.error('Error: No provers found')
            return None
        logger.info(f'Got Provers: {len(provers["provers"])}')

        
        # Step 5: Request challenge for each prover
        for prover in provers["provers"]:
            
            prover_id = prover["id"].split("/")[1]
            is_ip_v6 = True if prover["id"].split("/")[0] == "IPv6" else False
            latitude = int(prover["claims"]["latitude"] * 10**18)
            longitude = int(prover["claims"]["longitude"] * 10**18)
            
            if prover_id == "0x52374cce1bc1e2cd47c86e64e01bc0fd673c3639":
                request_id, challenges = submit_on_chain_request_for_challenge(
                                                                                    account,
                                                                                    chain_config,
                                                                                    proof_config,
                                                                                    prover_id,
                                                                                    is_ip_v6,
                                                                                    NUM_CHALLENGERS,
                                                                                    CHALLENGERS_TOLERANCE,
                                                                                    latitude,
                                                                                    longitude
                                                                                )
                logger.info(f'Request ID: {request_id} and challenges : {challenges}')
                for challenge in challenges:
                    if challenge:
                        logger.info(f'Triggering challenge for Prover: {prover["id"]} with challenge_id: {challenge}')
                        response = request_challenge(session,api_config, challenge)
                        if response:
                            logger.info(f'Status of challenge: {response}')


if __name__ == "__main__":
    main()
