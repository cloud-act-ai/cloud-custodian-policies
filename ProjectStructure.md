multi-cloud-cost-optimization/
├── README.md
├── Makefile
├── requirements.txt
├── c7n_policies/
│   ├── gcp/
│   │   ├── dev/
│   │   │   └── policies.yaml
│   │   ├── test/
│   │   │   └── policies.yaml
│   │   └── prod/
│   │       └── policies.yaml
│   └── azure/
│       ├── dev/
│       │   └── policies.yaml
│       ├── test/
│       │   └── policies.yaml
│       └── prod/
│           └── policies.yaml
├── src/
│   ├── analysis/
│   │   ├── bigquery_cost_analysis.py
│   │   ├── azure_cost_analysis.py
│   │   └── ...
│   └── policy_execution/
│       ├── run_gcp_policies.py
│       ├── run_azure_policies.py
│       └── ...
├── config/
│   ├── dev_config.yaml
│   ├── test_config.yaml
│   └── prod_config.yaml
└── scripts/
    ├── deploy.sh
    ├── run_analysis.sh
    └── run_custodian.sh
