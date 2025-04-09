# Multi-Cloud Cost Optimization with Cloud Custodian & Python

## Problem Statement

Organizations operating in multiple clouds (GCP, Azure) often struggle to manage costs effectively and maintain consistent governance. Common challenges include:
- Identifying idle or underutilized resources.
- Ensuring proper tagging/labeling for cost attribution.
- Automating corrective actions (stopping or terminating unused resources).
- Aggregating usage and cost data from different cloud providers for a unified view.

This repository provides a **production-ready** approach to address these challenges using **Cloud Custodian** (policy-as-code) and **Python** for cost analytics, with a reference folder structure, scripts, and automated workflows.

## Technical Details

1. **Cloud Custodian**: 
   - A policy-as-code engine for multi-cloud resource management.
   - We use [c7n[gcpext]](https://cloudcustodian.io/docs/quickstart/gcp.html) for GCP and [c7n[azure]](https://cloudcustodian.io/docs/azure/index.html) for Azure.
   - Policies are written in YAML and can be automatically enforced.

2. **Python Scripts**: 
   - Analyze cost and usage data from GCP (BigQuery billing export) and Azure (Cost Management APIs, or exported data in a storage account).
   - Provide daily/weekly cost breakdowns and resource utilization reports.

3. **Folder Structure**:
   - **c7n_policies/**: YAML policies separated by cloud and environment (dev, test, prod).
   - **src/analysis/**: Python files that query usage data (BigQuery, Azure Cost Management).
   - **src/policy_execution/**: Python orchestration scripts for running policies in each cloud.
   - **config/**: Environment-specific configuration (project IDs, subscription IDs, table/dataset names, etc.).
   - **Makefile**: For easy installation, execution of policies, and cost analysis jobs.

4. **CI/CD and Automation**:
   - Integrate with tools like GitHub Actions, GitLab CI, or Jenkins.
   - Use environment variables or secret managers to store and retrieve credentials securely.
   - Schedule policy runs and cost analyses (daily or weekly) for continuous cost governance.

## Installation

**Prerequisite**: Python 3.8+ is recommended.

1. **Clone this repository**:

    ```bash
    git clone https://github.com/your-org/multi-cloud-cost-optimization.git
    cd multi-cloud-cost-optimization
    ```

2. **Install Python dependencies**:

    You can either manually create a virtual environment or simply run:

    ```bash
    make install
    ```

    This will create a virtual environment (named `venv`), activate it, and install dependencies from `requirements.txt`.

## Authentication & Configuration

### GCP Setup

1. **Service Account**: Create a service account with BigQuery read permissions (for cost analysis) and any required resource permissions (for Cloud Custodian policies).
2. **Credentials**: Download the JSON key and set the environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
   ```

3. **Configuration File**: Update the configuration in `config/dev_config.yaml` (or other environment) with your GCP project ID and other relevant details.

## Available Policies

### BigQuery Cost Optimization

1. **BigQuery Tables Not Accessed (30+ days)**:
   - Identifies tables that haven't been accessed in over 30 days
   - Early warning system before tables become completely idle
   
2. **BigQuery Datasets Missing Required Labels**:
   - Detects datasets without required labels (env, owner, department)
   - Helps enforce tagging policies for better cost allocation
   
3. **BigQuery Datasets Without Logging**:
   - Finds datasets without access logging enabled
   - Helps maintain security compliance and monitor usage patterns
   
4. **Idle BigQuery Tables (90+ days)**:
   - Identifies tables not accessed in the last 90 days
   - Candidates for archiving to reduce storage costs
   
5. **Large Unpartitioned Tables**:
   - Detects tables larger than 10GB that are not partitioned
   - Helps optimize query performance and reduce costs

### Cloud Run Cost Optimization

1. **Underutilized Cloud Run Services**:
   - Finds services with low request counts (fewer than 1,000 in 30 days)
   - Identifies candidates for consolidation or removal
   
2. **Over-provisioned Cloud Run Services**:
   - Detects services with high memory allocation but low CPU utilization
   - Candidates for right-sizing to reduce costs
   
3. **Cloud Run Services with High Concurrency**:
   - Identifies services with high concurrency settings but limited CPU
   - Helps prevent performance issues and optimize resource allocation

### Compute Engine (VM) Cost Optimization

1. **VMs Missing Required Labels**:
   - Identifies VMs without required labels ('env' and 'owner')
   - Helps enforce tagging policies for better cost allocation
   
2. **Idle VMs with Low CPU Utilization**:
   - Detects running VMs with less than 10% average CPU utilization
   - Candidates for downsizing or termination
   
3. **VMs with No Network Activity**:
   - Identifies VMs with virtually no network traffic
   - Likely candidates for termination or investigation
   
4. **VMs with Moderate CPU Utilization**:
   - Finds VMs using between 10-50% of CPU
   - Candidates for rightsizing to a smaller machine type

5. **VMs with Oversized Disks**:
   - Detects VMs with low disk I/O operations
   - Potential candidates for disk resizing or storage type changes
   
6. **Long-Running Expensive VMs**:
   - Identifies high-cost VMs running for more than 30 days
   - Potential candidates for committed use discounts or custom machine types

## Running Policies

You can run the policies using several methods:

### Using Makefile:

Run all GCP policies:
```bash
make run-gcp
```

Run only BigQuery policies:
```bash
make run-bigquery
```

Run only Cloud Run policies:
```bash
make run-cloudrun
```

Run only Compute Engine (VM) policies:
```bash
make run-compute
```

Analyze a specific BigQuery dataset:
```bash
make run-dataset DATASET=my_dataset PROJECT=my-project-id
```

Analyze Cloud Run services in a specific region:
```bash
make run-region REGION=us-central1 PROJECT=my-project-id
```

Check VMs for missing required tags:
```bash
make run-vm-tags PROJECT=my-project-id
```

Check VMs for specific required tags:
```bash
make run-vm-tags PROJECT=my-project-id TAGS="env owner cost-center team"
```

Analyze all BigQuery datasets in a project:
```bash
make run-bq-project PROJECT=my-project-id
```

### Using Shell Script:

Run all policies:
```bash
./scripts/run_custodian.sh --cloud gcp --env dev
```

Run a specific policy file:
```bash
./scripts/run_custodian.sh --cloud gcp --env dev --policy bigquery_policies.yaml
```

### Using Python Scripts:

Analyze a specific BigQuery dataset:
```bash
./scripts/run_dataset_analysis.py --dataset my_dataset --project my-project-id
```

Analyze Cloud Run services in a specific region:
```bash
./scripts/run_region_analysis.py --region us-central1 --project my-project-id
```

### Troubleshooting

Common issues and solutions:

1. **Command not found: custodian**  
   This means Cloud Custodian is not in your PATH. The scripts have been configured to use the custodian command from the virtual environment. Make sure you've run `make install` first to create the virtual environment and install dependencies.

2. **FilterValidationError: metric-key not defined**  
   GCP metrics filters require a `metric-key` parameter that specifies how to map metrics to resources. This is already configured in the policies but might need adjustment based on the specific resource and metric.

3. **Access denied errors**  
   Ensure your service account has the proper permissions:
   - For BigQuery: `bigquery.datasets.get`, `bigquery.tables.list`, `bigquery.tables.get`
   - For Cloud Run: `run.services.list`, `run.services.get`, `monitoring.timeSeries.list`
   
4. **No results found**  
   - Check if your project has the resources you're targeting
   - Verify environment variables are correctly set
   - Use the `--dryrun` flag to test policies without executing actions
   
5. **Policy Actions**  
   - The policies are configured as read-only/analytical (no actions defined)
   - They will identify non-compliant resources without taking actions
   - If you want to add notify actions for alerting, you can edit the policies and add:
     ```yaml
     actions:
       - type: notify
         to:
           - email@example.com
         format: json
         subject: 'Alert Subject: {resource_attribute}'
         body: |
           Detailed information about the resource...
         transport:
           type: pubsub
           topic: projects/your-actual-project-id/topics/your-notification-topic
     ```

### Policy Output

After running the policies, you'll find the results in the `output/gcp/dev/YYYYMMDD_HHMMSS/` directory. Each policy generates:

- `resources.json`: List of resources that matched the policy filters
- `resources.html`: HTML report of the resources
- Logs and other execution details

## Adding New Policies

To add a new policy:

1. Create or edit the YAML file in `c7n_policies/gcp/[environment]/policies.yaml` or `c7n_policies/azure/[environment]/policies.yaml`
2. Follow the Cloud Custodian schema for the specific resource type
3. Test your policy with the `--dryrun` flag:

```bash
./venv/bin/custodian run --dryrun c7n_policies/gcp/dev/your-policy.yaml
```