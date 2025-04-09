#!/bin/bash
# Script to run Cloud Custodian policies

# Exit on error
set -e

# Default values
ENVIRONMENT="dev"
CLOUD="gcp"
POLICY_FILE=""

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --env|-e) ENVIRONMENT="$2"; shift ;;
        --cloud|-c) CLOUD="$2"; shift ;;
        --policy|-p) POLICY_FILE="$2"; shift ;;
        --help|-h) 
            echo "Usage: run_custodian.sh [OPTIONS]"
            echo "Run Cloud Custodian policies for GCP or Azure"
            echo ""
            echo "Options:"
            echo "  --env, -e ENV      Environment (dev, test, prod) [default: dev]"
            echo "  --cloud, -c CLOUD  Cloud provider (gcp, azure) [default: gcp]"
            echo "  --policy, -p FILE  Specific policy file to run [optional]"
            echo "  --help, -h         Show this help message and exit"
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Validate inputs
if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "test" && "$ENVIRONMENT" != "prod" ]]; then
    echo "Error: Environment must be one of: dev, test, prod"
    exit 1
fi

if [[ "$CLOUD" != "gcp" && "$CLOUD" != "azure" ]]; then
    echo "Error: Cloud must be one of: gcp, azure"
    exit 1
fi

# Set up paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
POLICY_DIR="$ROOT_DIR/c7n_policies/$CLOUD/$ENVIRONMENT"
OUTPUT_DIR="$ROOT_DIR/output/$CLOUD/$ENVIRONMENT/$(date +%Y%m%d_%H%M%S)"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Load configuration
CONFIG_FILE="$ROOT_DIR/config/${ENVIRONMENT}_config.yaml"
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Error: Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Source the virtual environment if it exists
if [[ -f "$ROOT_DIR/venv/bin/activate" ]]; then
    source "$ROOT_DIR/venv/bin/activate"
fi

# Run custodian
echo "Running Cloud Custodian for $CLOUD in $ENVIRONMENT environment"

if [[ -n "$POLICY_FILE" ]]; then
    # Run specific policy file
    FULL_POLICY_PATH="$POLICY_DIR/$POLICY_FILE"
    if [[ ! -f "$FULL_POLICY_PATH" ]]; then
        echo "Error: Policy file not found: $FULL_POLICY_PATH"
        exit 1
    fi
    
    echo "Running policy: $FULL_POLICY_PATH"
    "$ROOT_DIR/venv/bin/custodian" run --output-dir "$OUTPUT_DIR" "$FULL_POLICY_PATH"
else
    # Run all policies in the directory
    for policy_file in "$POLICY_DIR"/*.yaml "$POLICY_DIR"/*.yml; do
        if [[ -f "$policy_file" ]]; then
            echo "Running policy: $policy_file"
            "$ROOT_DIR/venv/bin/custodian" run --output-dir "$OUTPUT_DIR" "$policy_file"
        fi
    done
fi

echo "Execution complete. Results saved to: $OUTPUT_DIR"