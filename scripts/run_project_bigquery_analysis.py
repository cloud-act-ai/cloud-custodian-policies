#!/usr/bin/env python3
"""
Script to analyze all BigQuery datasets in a GCP project.
"""

import os
import sys
import subprocess
import json
import tempfile
import yaml
import argparse
from datetime import datetime

def run_bigquery_project_analysis(project_id, env="dev"):
    """Run analysis on all BigQuery datasets in a project."""
    
    print(f"Analyzing all BigQuery datasets in project: {project_id}")
    
    # Set up paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    policy_path = os.path.join(base_dir, f"c7n_policies/gcp/{env}/bigquery_policies.yaml")
    output_dir = os.path.join(base_dir, f"output/gcp/{env}/bigquery/{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    # Create the output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Set GCP project ID
    os.environ['GOOGLE_CLOUD_PROJECT'] = project_id
    
    # First, we need to list all datasets in the project
    try:
        # Path to custodian in virtual environment
        venv_dir = os.path.join(base_dir, "venv")
        python_cmd = os.path.join(venv_dir, "bin", "python3")
        
        # Create a temporary script to list all datasets
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_script_path = temp_file.name
            
            # Python script to list BigQuery datasets
            temp_file.write("""
import sys
from google.cloud import bigquery

project_id = sys.argv[1]
client = bigquery.Client(project=project_id)

datasets = list(client.list_datasets())
if datasets:
    print(json.dumps([dataset.dataset_id for dataset in datasets]))
else:
    print(json.dumps([]))
            """)
        
        # Execute the script to get datasets
        result = subprocess.run(
            [python_cmd, temp_script_path, project_id],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True
        )
        
        # Parse the dataset list
        datasets = json.loads(result.stdout.strip())
        
        if not datasets:
            print(f"No BigQuery datasets found in project: {project_id}")
            return False
        
        print(f"Found {len(datasets)} datasets in project {project_id}: {', '.join(datasets)}")
        
        # Now run analysis on each dataset
        for dataset_id in datasets:
            print(f"\nAnalyzing dataset: {dataset_id}")
            
            # Load the policy file
            with open(policy_path, 'r') as f:
                policy_data = yaml.safe_load(f)
            
            # Create a temporary policy file focused on this dataset
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_policy_file:
                temp_policy_path = temp_policy_file.name
                
                # Extract only the dataset analyzer policy and tables policies
                relevant_policies = []
                
                # Add the dataset analyzer policy
                for policy in policy_data['policies']:
                    if policy['name'] == 'bigquery-dataset-analyzer':
                        # Modify it to target this specific dataset
                        policy_copy = policy.copy()
                        policy_copy['filters'] = [
                            {
                                'type': 'value',
                                'key': 'datasetReference.datasetId',
                                'value': dataset_id
                            }
                        ]
                        policy_copy['name'] = f"bigquery-dataset-analyzer-{dataset_id}"
                        relevant_policies.append(policy_copy)
                
                # Add the dataset label check policy
                for policy in policy_data['policies']:
                    if policy['name'] == 'bigquery-datasets-missing-labels':
                        policy_copy = policy.copy()
                        policy_copy['filters'].append({
                            'type': 'value',
                            'key': 'datasetReference.datasetId',
                            'value': dataset_id
                        })
                        policy_copy['name'] = f"bigquery-datasets-missing-labels-{dataset_id}"
                        relevant_policies.append(policy_copy)
                
                # For tables, add a filter to only target this dataset
                table_policies = []
                for policy in policy_data['policies']:
                    if policy['resource'] == 'gcp.bq-table':
                        policy_copy = policy.copy()
                        # Add filter to only include tables from this dataset
                        policy_copy['filters'].append({
                            'type': 'value',
                            'key': 'tableReference.datasetId',
                            'value': dataset_id
                        })
                        policy_copy['name'] = f"{policy['name']}-{dataset_id}"
                        table_policies.append(policy_copy)
                
                # Combine all policies
                relevant_policies.extend(table_policies)
                
                # Create the new policy file
                new_policy_data = {'policies': relevant_policies}
                yaml_str = yaml.dump(new_policy_data)
                
                # Replace project_id placeholder
                yaml_str = yaml_str.replace('{project_id}', project_id)
                
                temp_policy_file.write(yaml_str)
            
            # Run custodian on this dataset in dryrun mode
            dataset_output_dir = os.path.join(output_dir, dataset_id)
            os.makedirs(dataset_output_dir, exist_ok=True)
            
            custodian_cmd = os.path.join(venv_dir, "bin", "custodian")
            cmd = [
                custodian_cmd, 
                "run", 
                "--dryrun",
                "--output-dir", dataset_output_dir,
                temp_policy_path
            ]
            
            print(f"Running command: {' '.join(cmd)}")
            
            try:
                result = subprocess.run(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    check=True
                )
                print(f"Successfully analyzed dataset: {dataset_id}")
            except subprocess.CalledProcessError as e:
                print(f"Error analyzing dataset {dataset_id}: {e}")
                print(f"Error output: {e.stderr}")
            finally:
                # Clean up the temporary policy file
                os.unlink(temp_policy_path)
        
        print(f"\nAnalysis complete for all datasets in project: {project_id}")
        print(f"Results saved to: {output_dir}")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"Error running script: {e}")
        print(f"Error output: {e.stderr}")
        return False
    finally:
        # Clean up temporary files
        if 'temp_script_path' in locals():
            os.unlink(temp_script_path)

def main():
    parser = argparse.ArgumentParser(description='Analyze all BigQuery datasets in a GCP project')
    parser.add_argument('--project', '-p', required=True, help='GCP project ID to analyze')
    parser.add_argument('--env', '-e', default='dev', choices=['dev', 'test', 'prod'], 
                        help='Environment to run policy in (default: dev)')
    
    args = parser.parse_args()
    
    run_bigquery_project_analysis(args.project, args.env)

if __name__ == "__main__":
    main()