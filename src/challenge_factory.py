from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from challenge import BaseChallenge, PoBChallenge, PoLChallenge

class ChallengeFactory:
    @staticmethod
    def create_challenge(challenge_type: str, chain_config: Dict[str, Any], 
                        proof_config: Dict[str, Any], src_path: str) -> BaseChallenge:
        """
        Create appropriate challenge instance based on type.
        
        Args:
            challenge_type: Type of proof (pol/pob)
            chain_config: Chain configuration dictionary
            proof_config: Proof configuration dictionary
            src_path: Source path for ABI files
            
        Returns:
            BaseChallenge: Instance of appropriate challenge class
        """
        if challenge_type.lower() == 'pol':
            return PoLChallenge(chain_config, proof_config, src_path)
        elif challenge_type.lower() == 'pob':
            return PoBChallenge(chain_config, proof_config, src_path)
        else:
            raise ValueError(f"Unsupported challenge type: {challenge_type}")