#!/usr/bin/env python3
"""
Script to run Cloud Custodian policies across multiple GCP projects.
"""

import os
import sys
import subprocess
import tempfile
import yaml
import argparse
import json
from datetime import datetime
import time

def load_config(environment="dev"):
    """Load environment-specific configuration."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, f"config/{environment}_config.yaml")
    
    if not os.path.exists(config_path):
        print(f"Error: Configuration file not found: {config_path}")
        return None
    
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def run_policy_for_project(project_id, policy_file, policy_type, env="dev"):
    """Run a Cloud Custodian policy for a specific GCP project."""
    
    print(f"\n{'='*80}")
    print(f"Running {policy_type} policies for project: {project_id}")
    print(f"{'='*80}")
    
    # Set up paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, f"output/gcp/{env}/{policy_type}/{project_id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Set GCP project ID as environment variable
    os.environ['GOOGLE_CLOUD_PROJECT'] = project_id
    os.environ['CLOUDSDK_CORE_PROJECT'] = project_id
    
    # Path to custodian in virtual environment
    venv_dir = os.path.join(base_dir, "venv")
    custodian_cmd = os.path.join(venv_dir, "bin", "custodian")
    
    # Load the policy file
    with open(policy_file, 'r') as f:
        policy_data = yaml.safe_load(f)
    
    # Create a temporary policy file with the project_id
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
        temp_policy_path = temp_file.name
        
        # Replace {project_id} with actual project ID
        yaml_str = yaml.dump(policy_data)
        yaml_str = yaml_str.replace('{project_id}', project_id)
        
        temp_file.write(yaml_str)
    
    try:
        # Run the policy in dryrun mode
        cmd = [
            custodian_cmd, 
            "run", 
            "--dryrun",
            "--output-dir", output_dir,
            temp_policy_path
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        if result.returncode != 0:
            print(f"Error running policy for project {project_id}:")
            print(f"Error output: {result.stderr}")
            return False
        
        print(f"Policy execution completed for project: {project_id}")
        print(f"Results saved to: {output_dir}")
        
        # Generate HTML reports
        generate_html_reports(output_dir)
        
        return True
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    
    finally:
        # Clean up the temporary file
        os.unlink(temp_policy_path)

def run_policy_for_dataset(project_id, dataset_id, env="dev"):
    """Run BigQuery policies for a specific dataset."""
    
    print(f"\n{'='*80}")
    print(f"Analyzing BigQuery dataset: {dataset_id} in project: {project_id}")
    print(f"{'='*80}")
    
    # Set up paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    policy_path = os.path.join(base_dir, f"c7n_policies/gcp/{env}/bigquery_policies.yaml")
    output_dir = os.path.join(base_dir, f"output/gcp/{env}/bigquery/{project_id}/{dataset_id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the policy file
    with open(policy_path, 'r') as f:
        policy_data = yaml.safe_load(f)
    
    # Create a temporary policy file with dataset_id and project_id
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
        temp_policy_path = temp_file.name
        
        # Replace placeholders
        yaml_str = yaml.dump(policy_data)
        yaml_str = yaml_str.replace('"$DATASET_ID"', f'"{dataset_id}"')
        yaml_str = yaml_str.replace('{project_id}', project_id)
        
        temp_file.write(yaml_str)
    
    try:
        # Set GCP project ID
        os.environ['GOOGLE_CLOUD_PROJECT'] = project_id
        os.environ['CLOUDSDK_CORE_PROJECT'] = project_id
        
        # Path to custodian command
        venv_dir = os.path.join(base_dir, "venv")
        custodian_cmd = os.path.join(venv_dir, "bin", "custodian")
        
        # Run the policy in dryrun mode
        cmd = [
            custodian_cmd, 
            "run", 
            "--dryrun",
            "--output-dir", output_dir,
            temp_policy_path
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        if result.returncode != 0:
            print(f"Error analyzing dataset {dataset_id} in project {project_id}:")
            print(f"Error output: {result.stderr}")
            return False
        
        print(f"Analysis completed for dataset: {dataset_id} in project: {project_id}")
        print(f"Results saved to: {output_dir}")
        
        # Generate HTML reports
        generate_html_reports(output_dir)
        
        return True
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    
    finally:
        # Clean up the temporary file
        os.unlink(temp_policy_path)

def generate_html_reports(output_dir):
    """Generate HTML reports for the output directory."""
    
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script_path = os.path.join(base_dir, "scripts/generate_html_reports.py")
        python_cmd = os.path.join(base_dir, "venv/bin/python3")
        
        cmd = [
            python_cmd,
            script_path,
            "--output-dir", output_dir
        ]
        
        print(f"Generating HTML reports for: {output_dir}")
        
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        if result.returncode != 0:
            print(f"Error generating HTML reports:")
            print(f"Error output: {result.stderr}")
            return False
        
        return True
    
    except Exception as e:
        print(f"Error generating HTML reports: {str(e)}")
        return False

def run_multi_project(policy_type, specific_projects=None, env="dev"):
    """Run policies across multiple projects."""
    
    config = load_config(env)
    if not config:
        print("Failed to load configuration.")
        return False
    
    # Get projects from config
    projects = []
    if specific_projects:
        # Filter to only specified projects
        for proj_id in specific_projects:
            projects.append({"id": proj_id})
    else:
        # Use all projects from config
        projects = config['gcp'].get('projects', [])
        if not projects:
            # Fall back to single project if projects list is empty
            projects = [{"id": config['gcp']['project_id']}]
    
    if not projects:
        print("No projects found in configuration.")
        return False
    
    # Set up paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Determine policy file based on type
    if policy_type == "compute":
        policy_file = os.path.join(base_dir, f"c7n_policies/gcp/{env}/compute_policies.yaml")
    elif policy_type == "cloudrun":
        policy_file = os.path.join(base_dir, f"c7n_policies/gcp/{env}/cloudrun_policies.yaml")
    elif policy_type == "bigquery":
        policy_file = os.path.join(base_dir, f"c7n_policies/gcp/{env}/bigquery_policies.yaml")
    else:
        print(f"Unsupported policy type: {policy_type}")
        return False
    
    # Verify policy file exists
    if not os.path.exists(policy_file):
        print(f"Policy file not found: {policy_file}")
        return False
    
    # Run policies for each project
    success_count = 0
    for project in projects:
        project_id = project["id"]
        if run_policy_for_project(project_id, policy_file, policy_type, env):
            success_count += 1
    
    print(f"\nCompleted policy execution for {success_count}/{len(projects)} projects.")
    return True

def run_multi_dataset(specific_projects=None, specific_datasets=None, env="dev"):
    """Run BigQuery policies across multiple datasets in multiple projects."""
    
    config = load_config(env)
    if not config:
        print("Failed to load configuration.")
        return False
    
    # Get datasets configuration
    datasets_config = config['gcp'].get('bigquery', {}).get('datasets', [])
    
    if not datasets_config and not specific_datasets:
        print("No datasets found in configuration and no specific datasets provided.")
        return False
    
    # Process datasets
    total_datasets = 0
    success_count = 0
    
    # If specific projects and datasets are provided
    if specific_projects and specific_datasets:
        for project_id in specific_projects:
            for dataset_id in specific_datasets:
                total_datasets += 1
                if run_policy_for_dataset(project_id, dataset_id, env):
                    success_count += 1
    
    # If only specific projects are provided, use datasets from config
    elif specific_projects:
        for project_config in datasets_config:
            if project_config['project_id'] in specific_projects:
                for dataset_id in project_config['datasets']:
                    total_datasets += 1
                    if run_policy_for_dataset(project_config['project_id'], dataset_id, env):
                        success_count += 1
    
    # If only specific datasets are provided, use all projects from config
    elif specific_datasets:
        for project_config in datasets_config:
            for dataset_id in specific_datasets:
                total_datasets += 1
                if run_policy_for_dataset(project_config['project_id'], dataset_id, env):
                    success_count += 1
    
    # If neither specific projects nor datasets are provided, use all from config
    else:
        for project_config in datasets_config:
            for dataset_id in project_config['datasets']:
                total_datasets += 1
                if run_policy_for_dataset(project_config['project_id'], dataset_id, env):
                    success_count += 1
    
    print(f"\nCompleted BigQuery analysis for {success_count}/{total_datasets} datasets.")
    return True

def main():
    parser = argparse.ArgumentParser(description='Run Cloud Custodian policies across multiple GCP projects')
    parser.add_argument('--type', '-t', required=True, choices=['compute', 'cloudrun', 'bigquery', 'all', 'datasets'],
                        help='Type of policies to run (compute, cloudrun, bigquery, all, or datasets)')
    parser.add_argument('--env', '-e', default='dev', choices=['dev', 'test', 'prod'],
                        help='Environment to run in (default: dev)')
    parser.add_argument('--projects', '-p', nargs='+', 
                        help='Specific project IDs to run policies on (default: all in config)')
    parser.add_argument('--datasets', '-d', nargs='+',
                        help='Specific BigQuery dataset IDs to analyze (for --type datasets)')
    
    args = parser.parse_args()
    
    if args.type == 'all':
        # Run all policy types
        for policy_type in ['compute', 'cloudrun', 'bigquery']:
            print(f"\n\n{'#'*80}")
            print(f"# Running {policy_type.upper()} policies")
            print(f"{'#'*80}")
            run_multi_project(policy_type, args.projects, args.env)
    elif args.type == 'datasets':
        # Run BigQuery dataset analysis
        run_multi_dataset(args.projects, args.datasets, args.env)
    else:
        # Run specific policy type
        run_multi_project(args.type, args.projects, args.env)

if __name__ == "__main__":
    main()