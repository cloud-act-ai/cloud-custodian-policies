#!/usr/bin/env python3
"""
Script to run BigQuery dataset analysis with Cloud Custodian.
"""

import os
import sys
import subprocess
import tempfile
import yaml
import argparse
from datetime import datetime

def run_policy_for_dataset(dataset_id, project_id, env="dev"):
    """Run BigQuery dataset analysis policy for a specific dataset."""
    
    print(f"Analyzing BigQuery dataset: {dataset_id} in project: {project_id}")
    
    # Set up paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    policy_path = os.path.join(base_dir, f"c7n_policies/gcp/{env}/bigquery_policies.yaml")
    output_dir = os.path.join(base_dir, f"output/gcp/{env}/bigquery/{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    # Create the output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the policy file
    with open(policy_path, 'r') as f:
        policy_data = yaml.safe_load(f)
    
    # Create a temporary policy file with the dataset_id replaced
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
        temp_policy_path = temp_file.name
        
        # Replace $DATASET_ID placeholder with the actual dataset ID
        yaml_str = yaml.dump(policy_data)
        yaml_str = yaml_str.replace('"$DATASET_ID"', f'"{dataset_id}"')
        
        # Add environment variables to policy
        yaml_str = yaml_str.replace('{project_id}', project_id)
        
        temp_file.write(yaml_str)
    
    try:
        # Set GCP project ID
        os.environ['GOOGLE_CLOUD_PROJECT'] = project_id
        
        # Path to custodian in virtual environment
        venv_dir = os.path.join(base_dir, "venv")
        custodian_cmd = os.path.join(venv_dir, "bin", "custodian")
        
        # Run the policy
        cmd = [
            custodian_cmd, 
            "run", 
            "--output-dir", output_dir,
            temp_policy_path
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True
        )
        
        print(f"Command output:\n{result.stdout}")
        print(f"Results saved to: {output_dir}")
        
    except subprocess.CalledProcessError as e:
        print(f"Error running policy: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)
    finally:
        # Clean up the temporary file
        os.unlink(temp_policy_path)

def main():
    parser = argparse.ArgumentParser(description='Run BigQuery dataset analysis for specific datasets')
    parser.add_argument('--dataset', '-d', required=True, help='BigQuery dataset ID to analyze')
    parser.add_argument('--project', '-p', required=True, help='GCP project ID containing the dataset')
    parser.add_argument('--env', '-e', default='dev', choices=['dev', 'test', 'prod'], 
                        help='Environment to run policy in (default: dev)')
    
    args = parser.parse_args()
    
    run_policy_for_dataset(args.dataset, args.project, args.env)

if __name__ == "__main__":
    main()