import os
import argparse
import time
import random
import requests
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple

from chain import get_web3_account,sign_message
from chain_connector import ChainConnector
from transaction_manager import TransactionManager
from prover_processor import ProverProcessor
from argument_parser import ArgumentParser
from proof_validations import validate_inputs

from config.config import Config
from api import create_pre_login_payload, get_pre_login_message, login, get_provers
from hexbytes import HexBytes
from logger import Logger


class ChallengeNetwork:
    def __init__(self, config_file: str, src_path: str):
        self.config = Config(config_file)
        self.src_path = src_path
        self.logger = Logger()

    def _authenticate(self, 
                     session: requests.Session, 
                     api_config: Dict[str, Any],
                     proof_config: Dict[str, Any],
                     account_config: Dict[str, Any],
                     proof_type: str,
                     account: Any) -> bool:
        """
        Authenticate with the API service.
        
        Args:
            session: Active requests session
            api_config: API configuration dictionary
            proof_config: Proof configuration dictionary
            account_config: Account configuration dictionary
            proof_type: Type of proof being requested
            account: Web3 account object
            
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            # Step 1: Get pre-login message
            pre_login_payload = create_pre_login_payload(
                account.address,
                proof_config,
                account_config,
                proof_type
            )
            
            message = get_pre_login_message(session, api_config, proof_type, pre_login_payload)
            if not message:
                self.logger.error('Pre-login failed')
                return False
            self.logger.info('Pre-login successful')

            # Step 2: Sign the message
            signed_message = sign_message(message, account)
            signed_payload = {
                "signature": signed_message.signature.hex()
            }

            # Step 3: Log in
            token = login(session, api_config, proof_type, signed_payload)
            if not token:
                self.logger.error('Error: Login failed')
                return False
            self.logger.info('Login successful')

            return True

        except Exception as e:
            self.logger.error(f'Authentication failed: {str(e)}')
            return False

    def _get_provers(self, 
                     session: requests.Session, 
                     api_config: Dict[str, Any],
                     proof_type: str,
                     prover_to_challenge: str) -> List[Dict[str, Any]]:
        """
        Get list of provers from the API.
        
        Args:
            session: Active requests session
            api_config: API configuration dictionary
            proof_type: Type of proof being requested
            prover_to_challenge: Specific prover to challenge or 'all'
            
        Returns:
            List of prover dictionaries
        """
        try:
            response = get_provers(session, api_config, proof_type)
            if not response or "provers" not in response:
                self.logger.error('Error: No provers found')
                return []
            
            provers = response["provers"]
            self.logger.info(f'Got Provers: {len(provers)}')
            
            # Shuffle provers for randomization
            random.shuffle(provers)
            
            # Filter provers if specific prover requested
            if prover_to_challenge != 'all':
                provers = list(filter(
                    lambda p: p["id"].split("/")[1] == prover_to_challenge, 
                    provers
                ))
                
            return provers

        except Exception as e:
            self.logger.error(f'Error getting provers: {str(e)}')
            return []

    def run(self, proof_type: str, private_key: str, **kwargs):
        api_config = self.config.get_api_config()
        chain_config = self.config.get_chain_config()
        proof_config = self.config.get_proof_config(proof_type)
        account_config = self.config.get_account_config()

        validate_inputs(proof_config)
        account = get_web3_account(private_key)

        with requests.Session() as session:
            session.headers.update(api_config["content_type_json"])
            
            if not self._authenticate(session, api_config, proof_config, 
                                    account_config, proof_type, account):
                return

            processor = ProverProcessor(
                session, 
                api_config, 
                chain_config, 
                proof_config,
                self.src_path  # Pass src_path to ProverProcessor
            )
            
            provers = self._get_provers(
                session, 
                api_config, 
                proof_type, 
                kwargs.get('prover_to_challenge', 'all')
            )
            
            if not provers:
                return

            for prover in provers:
                processor.process_prover(
                    proof_type, 
                    prover, 
                    account=account, 
                    **kwargs
                )

def main():
    args = ArgumentParser.parse_arguments()
    full_path = os.path.abspath(__file__)
    src_path = os.path.dirname(full_path) + "/"
    
    challenge_system = ChallengeNetwork(args.config_file, src_path)
    challenge_system.run(
        proof_type=args.proof_type,
        private_key=args.private_key,
        prover_to_challenge=args.prover,
        challenger_count=args.challenger_count,
        tolerance_count=args.tolerance_count,
        project_name=args.project_name,
        bandwidth_challenge_type=args.bandwidth_challenge_type
    )

if __name__ == "__main__":
    main()