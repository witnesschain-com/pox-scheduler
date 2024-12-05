import os
import argparse
import time
import random
import requests
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple

from chain import *
from chain_connector import ChainConnector
from transaction_manager import TransactionManager

from config.config import Config
from api import * 
from proof_validations import *
from hexbytes import HexBytes
from logger import Logger

class BaseChallenge(ABC):
    def __init__(self, chain_config: Dict[str, Any], proof_config: Dict[str, Any], src_path: str):
        self.chain_config = chain_config
        self.proof_config = proof_config
        self.chain_connector = ChainConnector(chain_config)
        self.transaction_manager = TransactionManager(chain_config, src_path)
        self.logger = Logger()

    @abstractmethod
    def encode_challenge(self, prover: str, **kwargs) -> bytes:
        pass

    def prepare_and_submit_request(self, account: str, challenge_info: bytes) -> Tuple[Dict, Any]:
        """Submit a challenge request transaction."""
        connection = self.chain_connector.get_rpc()
        return self.transaction_manager.prepare_and_submit_request_transaction(
            self.proof_config,
            connection,
            account,
            challenge_info
        )

    def process_logs(self, receipt: Dict, contract: Any) -> Tuple[int, List]:
        logs = contract.events.RequestProcessed().process_receipt(receipt)
        request_id = 0
        new_challenges = []
        
        for log in logs:
            request_id = log['args']['requestId']
            new_challenges = log['args']['newChallenges']
        
        return request_id, new_challenges

class PoLChallenge(BaseChallenge):
    def encode_challenge(self, prover: str, **kwargs) -> bytes:
        return eth_abi.encode(
            ["address", "address", "bool", "uint256", "uint256", "int256", "int256"],
            [
                self.chain_config["prover_registry"]["proxy"],
                prover,
                kwargs.get('is_ip_v6', False),
                kwargs.get('challengers_count') or self.proof_config["number_challengers_default"],
                kwargs.get('tolerance') or self.proof_config["challengers_tolerance_default"],
                kwargs.get('latitude', 0),
                kwargs.get('longitude', 0)
            ]
        )

class PoBChallenge(BaseChallenge):
    CHALLENGE_TYPES = {0: "downlink", 1: "uplink"}

    def encode_challenge(self, prover: str, **kwargs) -> bytes:
        return eth_abi.encode(
            ["address", "address", "uint", "bool", "uint256", "uint256", "uint256"],
            [
                self.chain_config["prover_registry"]["proxy"],
                prover,
                kwargs.get('bandwidth_challenge_type', 0),
                kwargs.get('is_ip_v6', False),
                kwargs.get('challengers_count') or self.proof_config["number_challengers_default"],
                kwargs.get('bandwidth', 0),
                kwargs.get('tolerance_count') or self.proof_config["challengers_tolerance_default"]
            ]
        )
