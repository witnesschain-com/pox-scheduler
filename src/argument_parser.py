from abc import ABC, abstractmethod
import argparse

class ArgumentParser:
    @staticmethod
    def parse_arguments():
        parser = argparse.ArgumentParser(description='Pass configuration file, proof type, number of challengers and tolerance level')
        
        # Add command line arguments
        parser.add_argument('--config_file', type=str,
                          help='The path to the configuration file (default: config/config.json) ')
        parser.add_argument('--proof_type', type=str,
                          help='The type of proof to run: pol / pob (default: pol)')
        parser.add_argument('--challenger_count', type=int, default=2,
                          help='Total # of challengers that should participate : (default: 2)')
        parser.add_argument('--tolerance_count', type=int, default=1,
                          help='Minimum # of challengers that should participate : (default: 1)')
        parser.add_argument('--private_key', type=str,
                          help='Private key of the payer : ')
        parser.add_argument('--prover', type=str, default='all',
                          help='Prover\'s address to challenge : (default: all )')
        parser.add_argument('--project_name', type=str, default='',
                          help='Prover\'s project name : ')
        parser.add_argument('--bandwidth_challenge_type', type=int, default=0,
                          help='Bandwidth Challenge Type (Downlink: 0 (default), Uplink: 1) : ')
        parser.add_argument('--network', type=str, default="testnet",
                          help='Network to run on (testnet or mainnet) (default is testnet ): ')
        
        args = parser.parse_args()
        
        # Interactive input for missing required arguments
        if not args.config_file:
            args.config_file = input('Please enter the path to the configuration file (default: config/config.json): ').strip() or 'config/config.json'
        if not args.proof_type:
            args.proof_type = input('Please enter the type of proof to run (default: pol): ').strip() or 'pol'
        if not args.private_key:
            args.private_key = input('Please enter the private key of the payer: ').strip()
        
        # Optional interactive inputs
        if args.challenger_count is None:
            args.challenger_count = int(input('Max # of challengers that can participate : (Default 2) ').strip() or '2')
        if args.tolerance_count is None:
            args.tolerance_count = int(input('Min # of challengers that can choose not to respond: (Default 1) ').strip() or '1')
        if not args.prover and not args.project_name:
            args.project_name = input('Please enter the prover\'s project name to challenge: ').strip().lower() or ''
        if args.proof_type.lower() == 'pob' and args.bandwidth_challenge_type is None:
            args.bandwidth_challenge_type = int(input('Please enter the Bandwidth Challenge Type (Downlink: 0 (Default), Uplink: 1): ').strip() or '0')
        if args.network.lower() not in ["testnet", "mainnet"]:
            args.network = input('Please enter one of 2 options (mainnet or testnet):').strip() or 'testnet'
        return args