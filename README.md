# PoX Challenge Scheduler

This script triggers PoX challenges, which are scheduled by a payer for the challenges. 
This README provides clear instructions for setting the private key, navigating to the appropriate directory, and running the script with the required arguments. 

It also includes an example command and notes to ensure proper setup and execution.


## Prerequisites

- Python 3.6 or higher

## Setup Guide

Follow these steps to set up and run the script:

### 0. Clone the repository
```sh
git clone https://github.com/witnesschain-com/pox-scheduler.git
```

### 1. Set Private Key

Export your private key as an environment variable. Make sure not to prefix it with `0x`.

```sh
export PRIVATE_KEY=<private_key> # Don't prefix with 0x
```

### 2. Navigate to the Source Directory
Change directory to the src directory where the script is located.
```sh
cd src
```

### 3. Run the Script
Run the pol_schedule.py script with the required arguments. You can ignore warnings by using the -W ignore flag.

```sh
python -W ignore pol_schedule.py --config_file config/config.json --proof_type pol --challenger_count 2 --tolerance_count 1
```
#### Arguments
    --config_file: The path to the configuration file (default: config/config.json).
    --proof_type: The type of proof to retrieve from the configuration (default: pol).
    --challenger_count: The number of challengers (default: 2).
    --tolerance_count: The tolerance count (default: 1).

#### Notes
Ensure that the ```config.json``` file exists and contains the correct configuration settings.
The script will prompt for any missing arguments if they are not provided.