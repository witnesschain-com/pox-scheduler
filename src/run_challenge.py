#### SET PRIVATE_KEY of the payer in your environment variables

import os
import argparse

from chain import *
from config.config import Config
from api import * 
from proof_validations import *
from hexbytes import HexBytes

import logging
import time

import random

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

def submit_on_chain_request_for_pol_challenge(
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
                                            SRC_PATH+chain_config["request_handler"]["abi_file_name_with_path"],
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

def should_run_for_prover(prover, prover_id, project_name=None, prover_to_challenge=None):
    if project_name:
        return prover["projectName"].lower() == project_name.lower()
    if prover_to_challenge:
        return prover_to_challenge.lower() in ('all', prover_id.lower())
    return False

def handle_challenge(session, api_config, proof_type, challenge, prover_id, request_id, poll_seconds):
    response = request_challenge(session, api_config, proof_type, prover_id, challenge)
    if not response:
        return

    logger.info(f'Challenge {challenge} for Prover {prover_id} (Request ID: {request_id}) - Status: {response["result"]["challenge_status"]}')
    
    challenge_id = response["result"]["challenge_id"]
    retries = 0
    
    while retries < api_config["retries"]:
        challenge_ended, status = has_challenge_ended(session, api_config, proof_type, challenge_id)
        logger.info(f'Status of challenge request for challenge_id : {challenge} - {status}')
        if challenge_ended:
            break
        retries += 1
        time.sleep(poll_seconds)
    
def process_prover( proof_type, 
                    prover, 
                    prover_to_challenge, 
                    project_name , 
                    session, 
                    api_config, 
                    account, 
                    chain_config, 
                    proof_config, 
                    challenger_count, 
                    tolerance_count, 
                    poll_seconds,
                    last_alive):
    try:
        prover_id = prover["id"].split("/")[1]
        is_ipv6 = prover["id"].split("/")[0] == "IPv6"
        
        if not (proof_type == 'pol' and 
                should_run_for_prover(prover, prover_id, project_name, prover_to_challenge) and 
                is_alive_yet(prover["last_alive"], last_alive)):
            logger.info(f'Skipping challenge for Prover: {prover["id"]} from {prover["projectName"].lower()}. Last alive at {prover["last_alive"]}')
            return

        latitude = int(prover["claims"]["latitude"] * 10**18)
        longitude = int(prover["claims"]["longitude"] * 10**18)
        
        request_id, challenges = submit_on_chain_request_for_pol_challenge(
            account, chain_config, proof_config, prover_id, is_ipv6,
            challenger_count, tolerance_count, latitude, longitude
        )

        for challenge in filter(None, challenges):
            logger.info(f'Triggering challenge for Prover: {prover["id"]} last alive at {prover["last_alive"]} with challenge_id: {challenge} and on-chain Request ID: {request_id}')
            handle_challenge(session, api_config, proof_type, challenge, prover["id"], request_id, poll_seconds)

    except KeyError:
        pass
    except Exception as e:
        logger.error(f"Error triggering for {prover}: {e}")

def main(config_file, proof_type,private_key,prover_to_challenge,challenger_count=1,tolerance_count=0,project_name='' ):

    config = Config(config_file)
        
    api_config = config.get_api_config()
    chain_config = config.get_chain_config()
    proof_config = config.get_proof_config(proof_type)
    account_config = config.get_account_config()

    poll_seconds = api_config["poll_seconds"]
    LAST_ALIVE = proof_config["alive_check_minutes"]


    validate_inputs(proof_config)
    
    account = get_web3_account(private_key)
    
    with requests.Session() as session:
        session.headers.update(api_config["content_type_json"])

        # Step 1: Get pre-login message
        pre_login_payload = create_pre_login_payload(account.address,proof_config,account_config,proof_type)
        message = get_pre_login_message(session, api_config, proof_type, pre_login_payload)
        if not message:
            logger.error('Pre-login failed: ')
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
        provers = get_provers(session, api_config, proof_type)["provers"]
        if not provers:
            logger.error('Error: No provers found')
            return None
        logger.info(f'Got Provers: {len(provers)}')        
        random.shuffle(provers)
        
        # Step 5: Request challenge for each prover
        for prover in provers:
            process_prover(proof_type, prover, prover_to_challenge, project_name, session, api_config, account, chain_config, proof_config, 
                        challenger_count, tolerance_count, poll_seconds, LAST_ALIVE)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Pass configuration file , proof type, number of challengers and tolerance level')
    parser.add_argument('--config_file', type=str, help='The path to the configuration file (default: config/config.json) ')
    parser.add_argument('--proof_type', type=str, help='The type of proof to run: pol / pob (default: pol)')
    parser.add_argument('--challenger_count', type=int, default=2, help='Total # of challengers that should participate : (default: 2)')
    parser.add_argument('--tolerance_count', type=int, default=1,help='Minimum # of challengers that should participate : (default: 1)')
    parser.add_argument('--private_key', type=str, help='Private key of the payer : ')
    parser.add_argument('--prover', type=str, default='all', help='Prover''s address to challenge : (default: all )')
    parser.add_argument('--project_name', type=str, default='', help='Prover''s project name : ')

    

    args = parser.parse_args()

    if not args.config_file:
        args.config_file = input('Please enter the path to the configuration file (default: config/config.json): ').strip() or 'config/config.json'
    if not args.proof_type:
        args.proof_type = input('Please enter the type of proof to run (default: pol): ').strip() or 'pol'
    if not args.challenger_count:
        args.challenger_count = int(input('Max # of challengers that can participate : (Default 2)').strip()) or 2
    if not args.tolerance_count:
        args.tolerance_count = int(input('Min # of challengers that can choose not to respond: (Default 1)').strip()) or 1
    if not args.private_key:
        args.private_key = input('Please enter the private key of the payer: ').strip() or ''
    if not args.prover:
        args.prover = input('Please enter the prover to challenge: ').strip() or ''
    if not args.project_name:
        args.project_name = input('Please enter the prover''s project name to challenge: ').strip().lower() or ''



    main(args.config_file, args.proof_type,args.private_key,args.prover,args.challenger_count,args.tolerance_count,args.project_name)