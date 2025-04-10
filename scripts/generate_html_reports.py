#!/usr/bin/env python3
"""
Script to generate HTML reports from Cloud Custodian JSON results.
"""

import os
import sys
import argparse
import subprocess
import json
import glob
from datetime import datetime

def generate_html_reports(output_dir):
    """Generate HTML reports for Cloud Custodian results in the specified directory."""
    
    print(f"Generating HTML reports for results in: {output_dir}")
    
    # Check if the directory exists
    if not os.path.exists(output_dir) or not os.path.isdir(output_dir):
        print(f"Error: Directory does not exist: {output_dir}")
        return False
    
    # Path to custodian in virtual environment
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_dir = os.path.join(base_dir, "venv")
    custodian_cmd = os.path.join(venv_dir, "bin", "custodian")
    
    # Find all policy directories
    policy_dirs = []
    # If specific policy directories are present
    for policy_dir in glob.glob(os.path.join(output_dir, "*")):
        if os.path.isdir(policy_dir) and os.path.exists(os.path.join(policy_dir, "resources.json")):
            policy_dirs.append(policy_dir)
    
    # If no specific policy directories, just use the directory itself
    if not policy_dirs and os.path.exists(os.path.join(output_dir, "resources.json")):
        policy_dirs.append(output_dir)
    
    if not policy_dirs:
        print("No resources.json files found in the specified directory.")
        return False
    
    for policy_dir in policy_dirs:
        policy_name = os.path.basename(policy_dir)
        resources_file = os.path.join(policy_dir, "resources.json")
        html_file = os.path.join(policy_dir, "report.html")
        
        # Check if resources.json exists and has content
        if not os.path.exists(resources_file):
            print(f"Skipping {policy_name}: no resources.json file found")
            continue
        
        with open(resources_file, 'r') as f:
            content = f.read().strip()
            if not content or content == "[]":
                print(f"Skipping {policy_name}: no resources found")
                continue
        
        # Create a simple HTML report
        with open(html_file, 'w') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloud Custodian Policy: {policy_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #3498db; margin-top: 40px; }}
        .resource {{ margin-bottom: 30px; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
        .resource:hover {{ background-color: #f8f9fa; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ text-align: left; padding: 12px; }}
        th {{ background-color: #3498db; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        pre {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow: auto; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Cloud Custodian Policy Results</h1>
        <p>Policy: {policy_name}</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
""")
            
            # Load the resources
            with open(resources_file, 'r') as res_file:
                resources = json.load(res_file)
            
            f.write(f"    <h2>Resources Found: {len(resources)}</h2>\n")
            
            # Add each resource
            for i, resource in enumerate(resources):
                f.write(f'    <div class="resource">\n')
                f.write(f'        <h3>Resource {i+1}</h3>\n')
                
                # Common attributes table
                common_attrs = ['name', 'id', 'creationTimestamp', 'status', 'zone', 'region', 'machineType']
                f.write('        <table>\n')
                f.write('            <tr><th>Attribute</th><th>Value</th></tr>\n')
                
                for attr in common_attrs:
                    if attr in resource:
                        value = resource[attr]
                        if isinstance(value, dict) or isinstance(value, list):
                            value = json.dumps(value, indent=2)
                        f.write(f'            <tr><td>{attr}</td><td>{value}</td></tr>\n')
                
                # Labels if available
                if 'labels' in resource:
                    f.write('            <tr><td>labels</td><td>')
                    if resource['labels']:
                        f.write('<ul>')
                        for k, v in resource['labels'].items():
                            f.write(f'<li>{k}: {v}</li>')
                        f.write('</ul>')
                    else:
                        f.write('No labels')
                    f.write('</td></tr>\n')
                
                f.write('        </table>\n')
                
                # Full JSON data
                f.write('        <h4>Full Resource Data</h4>\n')
                f.write(f'        <pre>{json.dumps(resource, indent=2)}</pre>\n')
                f.write('    </div>\n')
            
            f.write("""</body>
</html>""")
        
        print(f"Generated HTML report: {html_file}")
    
    print("\nAll HTML reports have been generated!")
    print(f"You can open them directly in a browser to view the results.")
    return True

def main():
    parser = argparse.ArgumentParser(description='Generate HTML reports from Cloud Custodian results')
    parser.add_argument('--output-dir', '-o', required=True, help='Directory containing Cloud Custodian results')
    
    args = parser.parse_args()
    
    generate_html_reports(args.output_dir)

if __name__ == "__main__":
    main()