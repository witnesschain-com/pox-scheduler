# PoX Challenge Scheduler

This script triggers PoX challenges, which are scheduled by a payer for the challenges. 
This README provides clear instructions for setting the private key, navigating to the appropriate directory, and running the script with the required arguments. 

It also includes an example command and notes to ensure proper setup and execution.


## Prerequisites

- Python 3.6 or higher
- Ideally 50 Challengers running to challenge the Prover

## Setup Guide

Follow these steps to set up and run the script:

### 0. Clone the repository
```sh
git clone https://github.com/witnesschain-com/pox-scheduler.git
```

### 1. Set Private Key

Export your private key as an environment variable. This is the account that will be signing the "submitRequest" transaction

```sh
export PRIVATE_KEY=<private_key>
```
> **Alert:** Make sure to replace `<private_key>`

### 2. Install the packages
Install the packages using pip
```sh
pip install -r requirements.txt
```


### 3. Navigate to the Source Directory
Change directory to the src directory where the script is located.
```sh
cd src
```

### 4. Run the Script
#### 4a. PoL Challenge

Run the ```run_challenge.py``` script with the required arguments to trigger a PoL Challenge. You can ignore warnings by using the -W ignore flag.

```sh
# Sample script to call a PoL challenge
python challenge_network.py --config_file config/config.json --proof_type pol --challenger_count 2 --private_key $PRIVATE_KEY --prover <PROVER_ADDRESS_TO_RUN_CHALLENGE_FOR>
```
#### Arguments
    --config_file: The path to the configuration file (default: config/config.json).
    --proof_type: The type of proof to retrieve from the configuration (pol or pob ; default: pol).
    --challenger_count: The number of challengers (default: 2).
    --private_key: Private Key of the account triggering the challenge (ECDSA Key starting with 0x)
    --prover: Prover address - Ethereum wallet (0x...)
    --project_name: Project Name (pingpong, eigenlayer) (optional)


#### Notes
Ensure that the ```config.json``` file exists and contains the correct configuration settings.
The script will prompt for any missing arguments if they are not provided.

#### 4b. PoB Challenge

```sh
# Sample script to call a PoB challenge
python challenge_network.py --config_file config/config.json --proof_type pob --challenger_count 5 --private_key $PRIVATE_KEY --prover <PROVER_ADDRESS_TO_RUN_CHALLENGE_FOR> --bandwidth_challenge_type <0/1>
```
#### Arguments
    --config_file: The path to the configuration file (default: config/config.json).
    --proof_type: The type of proof to retrieve from the configuration (pol or pob ; default: pol).
    --challenger_count: The number of challengers (default: 2).
    --private_key: Private Key of the account triggering the challenge  (ECDSA Key starting with 0x)
    --prover: Prover address - Ethereum wallet (0x...)
    --bandwidth_challenge_type: 0 -> Downlink, 1 -> Uplink


#### Notes
Ensure that the ```config.json``` file exists and contains the correct configuration settings.
The script will prompt for any missing arguments if they are not provided.