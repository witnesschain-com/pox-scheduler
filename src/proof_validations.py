def validate_inputs(proof_config):
    assert(proof_config["challenge_timeout_secs_minimum_default"] > 300)