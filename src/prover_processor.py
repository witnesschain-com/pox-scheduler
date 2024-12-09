from typing import Dict, List, Any, Optional, Tuple
import requests

from logger import Logger
from challenge_handler import ChallengeHandler
from challenge_factory import ChallengeFactory
from api import is_alive_yet

class ProverProcessor:
    def __init__(self, session: requests.Session, api_config: Dict[str, Any],
                 chain_config: Dict[str, Any], proof_config: Dict[str, Any], 
                 src_path: str):
        self.session = session
        self.api_config = api_config
        self.chain_config = chain_config
        self.proof_config = proof_config
        self.src_path = src_path
        self.challenge_handler = ChallengeHandler(session, api_config)
        self.logger = Logger()
        
    def should_run_for_prover(self, prover: Dict[str, Any], prover_id: str, 
                             project_name: Optional[str] = None, 
                             prover_to_challenge: Optional[str] = None) -> bool:
        """
        Determine if a challenge should be run for a specific prover.
        
        Args:
            prover: Dictionary containing prover information
            prover_id: Unique identifier for the prover
            project_name: Name of the project to filter by (optional)
            prover_to_challenge: Specific prover to challenge (optional)
            
        Returns:
            bool: True if should run challenge for this prover, False otherwise
        """
        try:
            if project_name:
                return (prover["projectName"].lower() == project_name.lower() or 
                       prover["projectName"].lower().startswith(project_name.lower()))
            if prover_to_challenge:
                return prover_to_challenge.lower() in ('all', prover_id.lower())
            return False
        except KeyError as e:
            self.logger.error(f"Missing required key in prover data: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error in should_run_for_prover: {e}")
            return False

    def _validate_prover(self, proof_type: str, prover: Dict, prover_id: str, **kwargs) -> bool:
        """
        Validate if the prover should be processed based on various criteria.
        
        Args:
            proof_type: Type of proof (pol/pob)
            prover: Prover information dictionary
            prover_id: Prover's unique identifier
            **kwargs: Additional arguments including project_name and prover_to_challenge
            
        Returns:
            bool: True if prover should be processed, False otherwise
        """
        try:
            # Check if proof type is valid
            if proof_type not in ['pol', 'pob']:
                self.logger.info(f'Invalid proof type: {proof_type}')
                return False

            # Check if prover should run based on project name or specific prover challenge
            if not self.should_run_for_prover(
                prover, 
                prover_id, 
                kwargs.get('project_name'), 
                kwargs.get('prover_to_challenge')
            ):
                self.logger.info(
                    f'Skipping challenge for Prover: {prover["id"]} from {prover["projectName"].lower()}. '
                    f'Last alive at {prover["last_alive"]}'
                )
                return False

            # Check if prover is alive within the specified time window
            if not is_alive_yet(prover["last_alive"], self.proof_config["alive_check_minutes"]):
                self.logger.info(f'Prover {prover_id} is not alive within the required time window')
                return False

            return True

        except KeyError as e:
            self.logger.error(f'Missing required key in prover data: {e}')
            return False
        except Exception as e:
            self.logger.error(f'Error validating prover {prover_id}: {e}')
            return False

    def _prepare_challenge_params(self, proof_type: str, prover: Dict, is_ipv6: bool, **kwargs) -> Dict:
        """
        Prepare challenge parameters based on proof type.
        
        Args:
            proof_type: Type of proof (pol/pob)
            prover: Prover information dictionary
            is_ipv6: Whether IPv6 is being used
            **kwargs: Additional challenge parameters
            
        Returns:
            Dict: Challenge parameters
        """
        base_params = {
            'is_ip_v6': is_ipv6,
            'challengers_count': kwargs.get('challenger_count'),
            'tolerance_count': kwargs.get('tolerance_count')
        }

        if proof_type == 'pol':
            return {
                **base_params,
                'latitude': int(prover["claims"]["latitude"] * 10**18),
                'longitude': int(prover["claims"]["longitude"] * 10**18)
            }
        else:  # pob
            bandwidth_type = kwargs.get('bandwidth_challenge_type', 0)
            bandwidth = (prover["claims"]["uplink_bandwidth"] 
                       if bandwidth_type 
                       else prover["claims"]["downlink_bandwidth"])
            return {
                **base_params,
                'bandwidth_challenge_type': bandwidth_type,
                'bandwidth': bandwidth
            }

    def _handle_challenge(self, proof_type: str, prover: Dict, challenge_id: str, 
                         request_id: str, **kwargs) -> None:
        """
        Handle a specific challenge for a prover.
        
        Args:
            proof_type: Type of proof (pol/pob)
            prover: Prover information dictionary
            challenge_id: Unique challenge identifier
            request_id: Request identifier
            **kwargs: Additional parameters
        """
        self.logger.info(
            f'Triggering {proof_type} challenge for Prover: {prover["id"]} '
            f'last alive at {prover["last_alive"]} with challenge_id: {challenge_id} '
            f'and on-chain Request ID: {request_id}'
        )
        
        challenge_type = (PoBChallenge.CHALLENGE_TYPES[kwargs.get('bandwidth_challenge_type', 0)] 
                         if proof_type == 'pob' else None)
        
        self.challenge_handler.handle_challenge(
            proof_type=proof_type,
            challenge_id=challenge_id,
            prover_id=prover["id"],
            request_id=request_id,
            poll_seconds=self.api_config["poll_seconds"],
            challenge_type=challenge_type
        )

    def process_prover(self, proof_type: str, prover: Dict, **kwargs) -> None:
        try:
            prover_id = prover["id"].split("/")[1]
            is_ipv6 = prover["id"].split("/")[0] == "IPv6"
            
            if not self._validate_prover(proof_type, prover, prover_id, **kwargs):
                return

            challenge = ChallengeFactory.create_challenge(
                proof_type, 
                self.chain_config, 
                self.proof_config,
                self.src_path
            )
            
            challenge_params = self._prepare_challenge_params(proof_type, prover, is_ipv6, **kwargs)
            receipt, contract = challenge.prepare_and_submit_request(
                kwargs['account'], 
                challenge.encode_challenge(prover_id, **challenge_params)
            )
            
            if receipt.get("status") != 1:
                self.logger.error(f'Challenge for Prover: {prover_id} failed. '
                                f'Txn Hash: {receipt["transactionHash"]}')
                return
            
            request_id, challenges = challenge.process_logs(receipt, contract)
            
            for challenge_id in filter(None, challenges):
                self._handle_challenge(proof_type, prover, challenge_id, request_id, **kwargs)
                
        except Exception as e:
            self.logger.error(f"Error processing prover {prover}: {e}")