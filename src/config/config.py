import json

class Config:
    def __init__(self, config_file):
        with open(config_file, 'r') as file:
            self.config = json.load(file)
        
    def get_api_config(self,network):
        return self.config['api'][network]

    def get_chain_config(self,network):
        return self.config['chain'][network]

    def get_proof_config(self,proof):
        return self.config['proofs'][proof]

    def get_account_config(self):
        return self.config['account']