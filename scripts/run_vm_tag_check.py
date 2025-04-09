#!/usr/bin/env python3
"""
Script to identify VMs without required tags in a specific GCP project.
"""

import os
import sys
import subprocess
import tempfile
import yaml
import argparse
from datetime import datetime

def run_vm_tag_check(project_id, required_tags=None, env="dev"):
    """Run Compute Engine VM tag check policy for a specific project."""
    
    if required_tags is None:
        required_tags = ["env", "owner"]
    
    print(f"Checking VMs in project: {project_id} for missing tags: {', '.join(required_tags)}")
    
    # Set up paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    policy_path = os.path.join(base_dir, f"c7n_policies/gcp/{env}/compute_policies.yaml")
    output_dir = os.path.join(base_dir, f"output/gcp/{env}/compute/{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    # Create the output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the policy file
    with open(policy_path, 'r') as f:
        policy_data = yaml.safe_load(f)
    
    # Create a temporary policy file with customized tag requirements
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
        temp_policy_path = temp_file.name
        
        # If we only care about the missing tags policy
        missing_tags_policy = None
        for policy in policy_data['policies']:
            if policy['name'] == 'gcp-vm-missing-required-labels':
                missing_tags_policy = policy
                break
        
        if missing_tags_policy:
            # Customize the policy for the specified tags
            filters = [{"or": []}]
            filters[0]["or"].append({"type": "value", "key": "labels", "value": None})
            
            for tag in required_tags:
                filters[0]["or"].append({
                    "type": "value", 
                    "key": f"labels.{tag}", 
                    "value": None
                })
            
            missing_tags_policy["filters"] = filters
            
            # Update the description and body to reflect the specific tags
            tag_list_str = ", ".join([f"'{tag}'" for tag in required_tags])
            missing_tags_policy["description"] = f"Identifies Google Compute Engine instances (VMs) that are missing required labels: {tag_list_str}."
            
            # Remove actions section completely
            if 'actions' in missing_tags_policy:
                del missing_tags_policy["actions"]
            
            # Create a new policies object with just this policy
            new_policies = {"policies": [missing_tags_policy]}
            yaml_str = yaml.dump(new_policies)
            
            # Replace project_id placeholder
            yaml_str = yaml_str.replace("{project_id}", project_id)
            
            temp_file.write(yaml_str)
        else:
            print("Error: Missing tags policy not found in policy file")
            sys.exit(1)
    
    try:
        # Set GCP project ID
        os.environ['GOOGLE_CLOUD_PROJECT'] = project_id
        
        # Path to custodian in virtual environment
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
            universal_newlines=True,
            check=True
        )
        
        print(f"Command output:\n{result.stdout}")
        print(f"Results saved to: {output_dir}")
        
        # Check if any resources were found
        resources_json_path = os.path.join(output_dir, "gcp-vm-missing-required-labels", "resources.json")
        if os.path.exists(resources_json_path):
            with open(resources_json_path, 'r') as f:
                resources = f.read().strip()
                if resources:
                    print("VMs without required tags were found. Check the output directory for details.")
                else:
                    print("Great! All VMs have the required tags.")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running policy: {e}")
        print(f"Error output: {e.stderr}")
        return False
    finally:
        # Clean up the temporary file
        os.unlink(temp_policy_path)

def main():
    parser = argparse.ArgumentParser(description='Check for GCP VMs missing required tags')
    parser.add_argument('--project', '-p', required=True, help='GCP project ID to check')
    parser.add_argument('--tags', '-t', nargs='+', default=['env', 'owner'], 
                        help='Required tags to check for (default: env owner)')
    parser.add_argument('--env', '-e', default='dev', choices=['dev', 'test', 'prod'], 
                        help='Environment to run policy in (default: dev)')
    
    args = parser.parse_args()
    
    run_vm_tag_check(args.project, args.tags, args.env)

if __name__ == "__main__":
    main()