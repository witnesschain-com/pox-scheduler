
from typing import Dict, List, Any, Optional, Tuple
from chain import *

class ChainConnector:
    def __init__(self, chain_config: Dict[str, Any]):
        self.chain_config = chain_config
        self.connection = None

    def get_rpc(self):
        if not self.connection:
            self.connection = connect_to_rpc(self.chain_config["rpc_url"])
            if not self.connection:
                raise ConnectionError(f"Unable to connect to {self.chain_config['rpc_url']}")
        return self.connection