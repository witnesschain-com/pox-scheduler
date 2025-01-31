import time
#import requests
from custom_session import CustomSession

from typing import Dict, List, Any, Optional, Tuple

from api import request_challenge, has_challenge_ended
from logger import Logger

class ChallengeHandler:
    def __init__(self, session: CustomSession, api_config: Dict[str, Any]):
        self.session = session
        self.api_config = api_config
        self.logger = Logger()

    def handle_challenge(self, proof_type: str, challenge_id: str, prover_id: str, 
                        request_id: str, poll_seconds: int, challenge_type: str) -> None:
        response = request_challenge(self.session, self.api_config, proof_type, 
                                  prover_id, challenge_id, challenge_type)
        if not response:
            return

        self.logger.info(f'Challenge {challenge_id} for Prover {prover_id} '
                        f'(Request ID: {request_id}) - Status: {response["result"]["challenge_status"]}')
        
        retries = 0
        while retries < self.api_config["retries"]:
            challenge_ended, status = has_challenge_ended(self.session, self.api_config, 
                                                       proof_type, challenge_id)
            self.logger.info(f'Status of challenge request for challenge_id : {challenge_id} - {status}')
            
            if challenge_ended:
                return
            
            retries += 1
            time.sleep(poll_seconds)