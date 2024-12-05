from typing import Dict, List, Any, Optional, Tuple
from chain import submit_transaction
from logger import Logger

class TransactionManager:
    """Handles blockchain transaction preparation and submission."""
    
    def __init__(self, chain_config: Dict[str, Any], src_path: str):
        self.chain_config = chain_config
        self.src_path = src_path
        self.logger = Logger()

    def prepare_and_submit_request_transaction(
            self,
            proof_config: Dict[str, Any],
            connection_to_rpc: Any,
            account: Any,
            challenge_info: bytes
    ) -> Tuple[Dict, Any]:
        """
        Prepare and submit a blockchain transaction for a challenge request.
        
        Args:
            proof_config: Configuration for the proof type
            connection_to_rpc: RPC connection to the blockchain
            account: Account to submit the transaction from
            challenge_info: Encoded challenge information
            
        Returns:
            Tuple[Dict, Any]: Transaction receipt and contract instance
        """
        try:
            receipt, contract = submit_transaction(
                self.chain_config["chain_id"],
                connection_to_rpc,
                self.chain_config["gas_limit"],
                account,
                self.chain_config["request_handler"]["proxy"],
                self.src_path + self.chain_config["request_handler"]["abi_file_name_with_path"],
                "submitRequest",
                proof_config["challenge_timeout_secs_minimum_default"],
                proof_config["attribute_ids"],
                [challenge_info]
            )
            return receipt, contract
            
        except Exception as e:
            self.logger.error(f"Error submitting transaction: {e}")
            raise