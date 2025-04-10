#!/usr/bin/env python3
"""
Script to execute Cloud Custodian policies for GCP resources.
"""

import os
import subprocess
import yaml
import logging
import argparse
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"custodian_gcp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger('custodian-gcp')

def load_config(environment):
    """Load environment-specific configuration."""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        f"config/{environment}_config.yaml"
    )
    
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def run_custodian(policy_file, output_dir, config):
    """Run Cloud Custodian with the specified policy file."""
    # Set GCP project ID as environment variable
    os.environ['GOOGLE_CLOUD_PROJECT'] = config['gcp']['project_id']
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Get the path to the custodian command in the virtual environment
    venv_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'venv')
    custodian_cmd = os.path.join(venv_dir, 'bin', 'custodian')
    
    # Construct the custodian command with dryrun flag
    cmd = [
        custodian_cmd, 'run',
        '--dryrun',
        '--output-dir', output_dir,
        policy_file
    ]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True
        )
        logger.info(f"Command output:\n{result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}")
        logger.error(f"Error output:\n{e.stderr}")
        return False

def main():
    """Main function to execute GCP policies."""
    parser = argparse.ArgumentParser(description='Run Cloud Custodian policies for GCP')
    parser.add_argument('--env', '-e', default='dev', choices=['dev', 'test', 'prod'],
                        help='Environment to run policies in (default: dev)')
    args = parser.parse_args()
    
    try:
        # Load configuration for the specified environment
        config = load_config(args.env)
        
        # Set up paths
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        policy_dir = os.path.join(base_dir, f"c7n_policies/gcp/{args.env}")
        output_dir = os.path.join(base_dir, f"output/gcp/{args.env}/{datetime.now().strftime('%Y%m%d')}")
        
        logger.info(f"Running GCP policies for environment: {args.env}")
        
        # Find all policy files in the policy directory
        policy_files = [os.path.join(policy_dir, f) for f in os.listdir(policy_dir) 
                       if f.endswith(('.yaml', '.yml'))]
        
        logger.info(f"Found {len(policy_files)} policy files: {', '.join([os.path.basename(f) for f in policy_files])}")
        
        if not policy_files:
            logger.warning(f"No policy files found in {policy_dir}")
            return
        
        # Execute each policy file
        success_count = 0
        for policy_file in policy_files:
            logger.info(f"Processing policy file: {policy_file}")
            if run_custodian(policy_file, output_dir, config):
                success_count += 1
                
        logger.info(f"Completed policy execution. {success_count}/{len(policy_files)} policies executed successfully.")
        
    except Exception as e:
        logger.exception(f"An error occurred during policy execution: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()