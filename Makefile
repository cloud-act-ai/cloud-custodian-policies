.PHONY: install run-gcp run-azure run-analysis run-bigquery run-cloudrun

# Variables
VENV_NAME = venv
PYTHON = $(VENV_NAME)/bin/python3
PIP = $(VENV_NAME)/bin/pip3
CUSTODIAN = $(VENV_NAME)/bin/custodian

install:
	@echo "Creating virtual environment and installing dependencies..."
	python3 -m venv $(VENV_NAME)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run-gcp:
	@echo "Running all GCP policies..."
	$(PYTHON) src/policy_execution/run_gcp_policies.py

run-azure:
	@echo "Running Azure policies..."
	$(PYTHON) src/policy_execution/run_azure_policies.py

run-bigquery:
	@echo "Running only BigQuery policies..."
	$(CUSTODIAN) run --dryrun --output-dir output/gcp/dev/bigquery/$(shell date +%Y%m%d_%H%M%S) c7n_policies/gcp/dev/bigquery_policies.yaml

run-cloudrun:
	@echo "Running only Cloud Run policies..."
	$(CUSTODIAN) run --dryrun --output-dir output/gcp/dev/cloudrun/$(shell date +%Y%m%d_%H%M%S) c7n_policies/gcp/dev/cloudrun_policies.yaml
	
run-compute:
	@echo "Running only Compute Engine (VM) policies..."
	$(CUSTODIAN) run --dryrun --output-dir output/gcp/dev/compute/$(shell date +%Y%m%d_%H%M%S) c7n_policies/gcp/dev/compute_policies.yaml

run-dataset:
	@echo "Running BigQuery dataset analysis..."
	@if [ -z "$(DATASET)" ]; then \
		echo "Error: DATASET parameter is required. Usage: make run-dataset DATASET=your_dataset_id PROJECT=your_project_id"; \
		exit 1; \
	fi
	@if [ -z "$(PROJECT)" ]; then \
		echo "Error: PROJECT parameter is required. Usage: make run-dataset DATASET=your_dataset_id PROJECT=your_project_id"; \
		exit 1; \
	fi
	$(PYTHON) scripts/run_dataset_analysis.py --dataset $(DATASET) --project $(PROJECT)
	
run-bq-project:
	@echo "Analyzing all BigQuery datasets in project..."
	@if [ -z "$(PROJECT)" ]; then \
		echo "Error: PROJECT parameter is required. Usage: make run-bq-project PROJECT=your_project_id"; \
		exit 1; \
	fi
	$(PYTHON) scripts/run_project_bigquery_analysis.py --project $(PROJECT)

run-region:
	@echo "Running Cloud Run region analysis..."
	@if [ -z "$(REGION)" ]; then \
		echo "Error: REGION parameter is required. Usage: make run-region REGION=us-central1 PROJECT=your_project_id"; \
		exit 1; \
	fi
	@if [ -z "$(PROJECT)" ]; then \
		echo "Error: PROJECT parameter is required. Usage: make run-region REGION=us-central1 PROJECT=your_project_id"; \
		exit 1; \
	fi
	$(PYTHON) scripts/run_region_analysis.py --region $(REGION) --project $(PROJECT)
	
run-vm-tags:
	@echo "Checking VMs for missing required tags..."
	@if [ -z "$(PROJECT)" ]; then \
		echo "Error: PROJECT parameter is required. Usage: make run-vm-tags PROJECT=your_project_id [TAGS='env owner cost-center']"; \
		exit 1; \
	fi
	@if [ -z "$(TAGS)" ]; then \
		$(PYTHON) scripts/run_vm_tag_check.py --project $(PROJECT); \
	else \
		$(PYTHON) scripts/run_vm_tag_check.py --project $(PROJECT) --tags $(TAGS); \
	fi

run-analysis:
	@echo "Running cost analysis..."
	$(PYTHON) src/analysis/bigquery_cost_analysis.py
	$(PYTHON) src/analysis/azure_cost_analysis.py

clean:
	@echo "Cleaning up..."
	rm -rf $(VENV_NAME)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete