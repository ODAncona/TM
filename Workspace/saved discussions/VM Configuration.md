# Python + Hydra for HPC Scheduler Benchmarking

You're absolutely right - Python with Hydra is an excellent choice for managing complex configurations in this scenario. This approach offers significant advantages over shell scripts, particularly for a research project involving multiple configurations and parameters.

## Revised Architecture with Python + Hydra

```
┌─────────────────────────────────────────────────────┐
│ Python Orchestration Layer with Hydra               │
│                                                     │
│ ┌─────────────────┐      ┌─────────────────────┐    │
│ │ Config Structure│      │ Experiment Runner   │    │
│ │ - Topologies    │      │ - Provision         │    │
│ │ - Schedulers    │──────│ - Configure         │    │
│ │ - Workloads     │      │ - Benchmark         │    │
│ │ - Parameters    │      │ - Collect metrics   │    │
│ └─────────────────┘      └─────────────────────┘    │
└─────────────────────────────────────────────────────┘
            │                       │
┌───────────▼───────────┐  ┌────────▼────────────────┐
│ Terraform             │  │ Ansible                 │
│ (Infrastructure)      │  │ (Configuration)         │
└─────────────────────────┘  └─────────────────────────┘
```

## Implementation with Hydra

### 1. Directory Structure

```
benchmark-project/
├── conf/                          # Hydra configuration files
│   ├── config.yaml                # Base configuration
│   ├── topology/                  # Infrastructure topologies
│   │   ├── small.yaml
│   │   ├── medium.yaml
│   │   └── large.yaml
│   ├── scheduler/                 # Scheduler configurations
│   │   ├── slurm.yaml
│   │   ├── kubernetes.yaml
│   │   └── flux.yaml
│   ├── workload/                  # Workload patterns
│   │   ├── cpu_intensive.yaml
│   │   ├── gpu_intensive.yaml
│   │   └── mixed.yaml
│   └── experiment/                # Experiment configurations
│       ├── full_matrix.yaml
│       └── selected_tests.yaml
├── terraform/                     # Terraform files
│   ├── main.tf
│   └── modules/...
├── ansible/                       # Ansible files
│   ├── playbooks/...
│   └── roles/...
├── src/                           # Python source code
│   ├── __init__.py
│   ├── main.py                    # Main entry point
│   ├── infrastructure.py          # Infrastructure management
│   ├── configuration.py           # System configuration
│   ├── benchmark.py               # Benchmark execution
│   └── metrics.py                 # Metrics collection
├── requirements.txt               # Python dependencies
└── README.md
```

### 2. Base Configuration (conf/config.yaml)

```yaml
# @package _global_

defaults:
  - topology: medium
  - scheduler: slurm
  - workload: mixed
  - _self_

# General settings
project_name: hpc-scheduler-benchmark
output_dir: ${hydra:runtime.cwd}/outputs/${now:%Y-%m-%d}/${topology}_${scheduler}_${workload}

# Infrastructure settings
base_image_path: "/path/to/base/image.qcow2"
network_cidr: "10.0.100.0/24"

# Benchmark settings
benchmark_duration: 3600  # seconds
metrics_interval: 5       # seconds
repetitions: 3

# Terraform settings
terraform_dir: ${hydra:runtime.cwd}/terraform

# Ansible settings
ansible_dir: ${hydra:runtime.cwd}/ansible
```

### 3. Topology Configuration (conf/topology/medium.yaml)

```yaml
# @package _group_

name: medium
description: "Medium-sized cluster with 1 head node and 8 compute nodes"

head_nodes:
  count: 1
  vcpu: 8
  memory: 16384
  disk: 100

compute_nodes:
  count: 8
  vcpu: 16
  memory: 32768
  disk: 200
  
network:
  internal_subnet: "10.0.100.0/24"
  
storage:
  shared_nfs: true
  nfs_size: 500  # GB
```

### 4. Scheduler Configuration (conf/scheduler/slurm.yaml)

```yaml
# @package _group_

name: slurm
version: "21.08.8"

config:
  accounting_storage_type: "accounting_storage/none"
  scheduler_type: "sched/backfill"
  select_type: "select/cons_tres"
  proctrack_type: "proctrack/cgroup"
  task_plugin: "task/cgroup"
  
plugins:
  - "topology/tree"
  - "select/cons_tres"
  
parameters:
  max_array_size: 1000
  scheduler_min_interval: 2
  
tuning:
  scheduler_threads: 2
```

### 5. Main Python Script (src/main.py)

```python
#!/usr/bin/env python3
import os
import sys
import logging
from pathlib import Path
import hydra
from omegaconf import DictConfig, OmegaConf

from src.infrastructure import provision_infrastructure, teardown_infrastructure
from src.configuration import configure_scheduler
from src.benchmark import run_benchmarks
from src.metrics import collect_metrics, analyze_results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@hydra.main(config_path="../conf", config_name="config")
def main(cfg: DictConfig) -> None:
    """Main entry point for the HPC scheduler benchmark."""
    logger.info(f"Starting benchmark with configuration:\n{OmegaConf.to_yaml(cfg)}")
    
    try:
        # Step 1: Provision infrastructure based on topology
        logger.info(f"Provisioning {cfg.topology.name} infrastructure...")
        infra_details = provision_infrastructure(cfg)
        
        # Step 2: Configure selected scheduler
        logger.info(f"Configuring {cfg.scheduler.name} on infrastructure...")
        scheduler_details = configure_scheduler(cfg, infra_details)
        
        # Step 3: Run benchmarks with selected workload
        logger.info(f"Running {cfg.workload.name} benchmarks...")
        for i in range(cfg.repetitions):
            logger.info(f"Starting benchmark run {i+1}/{cfg.repetitions}")
            benchmark_results = run_benchmarks(cfg, infra_details, scheduler_details)
            
            # Step 4: Collect and store metrics
            logger.info("Collecting metrics...")
            metrics = collect_metrics(cfg, benchmark_results)
            
            # Save results for this run
            result_dir = Path(cfg.output_dir) / f"run_{i+1}"
            result_dir.mkdir(parents=True, exist_ok=True)
            OmegaConf.save(OmegaConf.create(metrics), result_dir / "metrics.yaml")
        
        # Step 5: Analyze results across runs
        logger.info("Analyzing results...")
        analysis = analyze_results(cfg.output_dir)
        
        logger.info(f"Benchmark completed successfully. Results in {cfg.output_dir}")
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}", exc_info=True)
        return 1
    finally:
        # Clean up infrastructure if not in debug mode
        if not cfg.get("debug", False):
            logger.info("Tearing down infrastructure...")
            teardown_infrastructure(cfg, infra_details)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### 6. Infrastructure Management (src/infrastructure.py)

```python
import os
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Any
from omegaconf import DictConfig

logger = logging.getLogger(__name__)

def provision_infrastructure(cfg: DictConfig) -> Dict[str, Any]:
    """Provision infrastructure using Terraform based on configuration."""
    terraform_dir = Path(cfg.terraform_dir)
    
    # Create variables file from Hydra config
    tf_vars = {
        "topology_name": cfg.topology.name,
        "head_node_count": cfg.topology.head_nodes.count,
        "head_node_vcpu": cfg.topology.head_nodes.vcpu,
        "head_node_memory": cfg.topology.head_nodes.memory,
        "compute_node_count": cfg.topology.compute_nodes.count,
        "compute_node_vcpu": cfg.topology.compute_nodes.vcpu,
        "compute_node_memory": cfg.topology.compute_nodes.memory,
        "base_image_path": cfg.base_image_path,
        "network_cidr": cfg.network_cidr
    }
    
    with open(terraform_dir / "terraform.tfvars.json", "w") as f:
        json.dump(tf_vars, f, indent=2)
    
    # Initialize and apply Terraform
    subprocess.run(["terraform", "init"], cwd=terraform_dir, check=True)
    subprocess.run(["terraform", "apply", "-auto-approve"], cwd=terraform_dir, check=True)
    
    # Get output from Terraform
    result = subprocess.run(
        ["terraform", "output", "-json"], 
        cwd=terraform_dir, 
        check=True, 
        capture_output=True, 
        text=True
    )
    
    # Parse Terraform output
    infra_details = json.loads(result.stdout)
    
    # Save infrastructure details to output directory
    os.makedirs(cfg.output_dir, exist_ok=True)
    with open(f"{cfg.output_dir}/infrastructure.json", "w") as f:
        json.dump(infra_details, f, indent=2)
    
    return infra_details

def teardown_infrastructure(cfg: DictConfig, infra_details: Dict[str, Any]) -> None:
    """Tear down infrastructure using Terraform."""
    terraform_dir = Path(cfg.terraform_dir)
    
    # Destroy infrastructure
    subprocess.run(["terraform", "destroy", "-auto-approve"], cwd=terraform_dir, check=True)
    
    logger.info("Infrastructure destroyed successfully")
```

### 7. Scheduler Configuration (src/configuration.py)

```python
import os
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Any
from omegaconf import DictConfig, OmegaConf

logger = logging.getLogger(__name__)

def configure_scheduler(cfg: DictConfig, infra_details: Dict[str, Any]) -> Dict[str, Any]:
    """Configure the selected scheduler on the infrastructure."""
    ansible_dir = Path(cfg.ansible_dir)
    
    # Create Ansible inventory from infrastructure details
    create_ansible_inventory(ansible_dir, infra_details)
    
    # Create scheduler-specific variables
    scheduler_vars = {
        "scheduler_name": cfg.scheduler.name,
        "scheduler_version": cfg.scheduler.version,
        "scheduler_config": OmegaConf.to_container(cfg.scheduler.config),
        "scheduler_plugins": cfg.scheduler.plugins,
        "scheduler_parameters": OmegaConf.to_container(cfg.scheduler.parameters),
        "scheduler_tuning": OmegaConf.to_container(cfg.scheduler.tuning),
        "topology": OmegaConf.to_container(cfg.topology)
    }
    
    # Write scheduler variables to file
    vars_file = ansible_dir / "vars" / "scheduler_vars.json"
    os.makedirs(os.path.dirname(vars_file), exist_ok=True)
    with open(vars_file, "w") as f:
        json.dump(scheduler_vars, f, indent=2)
    
    # Run Ansible playbook for the selected scheduler
    playbook = f"configure_{cfg.scheduler.name}.yml"
    subprocess.run(
        [
            "ansible-playbook", 
            "-i", "inventory/hosts.yml", 
            f"playbooks/{playbook}",
            "-e", f"@vars/scheduler_vars.json"
        ], 
        cwd=ansible_dir, 
        check=True
    )
    
    # Verify configuration
    result = subprocess.run(
        [
            "ansible-playbook", 
            "-i", "inventory/hosts.yml", 
            "playbooks/verify_configuration.yml",
            "-e", f"scheduler={cfg.scheduler.name}"
        ], 
        cwd=ansible_dir, 
        check=True,
        capture_output=True,
        text=True
    )
    
    # Parse verification results
    scheduler_details = {
        "configuration_status": "configured",
        "verification_output": result.stdout
    }
    
    # Save configuration details to output directory
    with open(f"{cfg.output_dir}/scheduler_configuration.json", "w") as f:
        json.dump(scheduler_details, f, indent=2)
    
    return scheduler_details

def create_ansible_inventory(ansible_dir: Path, infra_details: Dict[str, Any]) -> None:
    """Create Ansible inventory file from infrastructure details."""
    inventory = {
        "all": {
            "children": {
                "head_nodes": {
                    "hosts": {}
                },
                "compute_nodes": {
                    "hosts": {}
                }
            }
        }
    }
    
    # Add head nodes to inventory
    for node in infra_details["head_nodes"]["value"]:
        inventory["all"]["children"]["head_nodes"]["hosts"][node["name"]] = {
            "ansible_host": node["ip_address"],
            "ansible_user": "ubuntu",
            "vcpus": node["vcpus"],
            "memory": node["memory"]
        }
    
    # Add compute nodes to inventory
    for node in infra_details["compute_nodes"]["value"]:
        inventory["all"]["children"]["compute_nodes"]["hosts"][node["name"]] = {
            "ansible_host": node["ip_address"],
            "ansible_user": "ubuntu",
            "vcpus": node["vcpus"],
            "memory": node["memory"]
        }
    
    # Write inventory to file
    inventory_file = ansible_dir / "inventory" / "hosts.yml"
    os.makedirs(os.path.dirname(inventory_file), exist_ok=True)
    with open(inventory_file, "w") as f:
        json.dump(inventory, f, indent=2)
```

### 8. Running Multi-Configuration Experiments

You can define experiment configurations that run multiple combinations:

```yaml
# conf/experiment/full_matrix.yaml
# Full matrix of all topologies, schedulers, and workloads

defaults:
  - override /topology: small
  - override /scheduler: slurm
  - override /workload: cpu_intensive
  - _self_

hydra:
  sweeper:
    params:
      topology: small,medium,large
      scheduler: slurm,kubernetes,flux
      workload: cpu_intensive,gpu_intensive,mixed
  sweep:
    dir: multirun/${now:%Y-%m-%d}
    subdir: ${topology}_${scheduler}_${workload}
```

Run with:
```bash
python src/main.py --multirun --config-name=experiment/full_matrix
```

## Benefits of Python + Hydra Approach

1. **Structured Configuration Management**: Hydra excels at managing complex, hierarchical configurations
2. **Composition**: Mix and match configurations (topologies, schedulers, workloads)
3. **Parameter Sweeping**: Easily run experiments across the entire parameter space
4. **Reproducibility**: Configurations are versioned and can be saved with results
5. **Logging & Monitoring**: Better error handling and progress tracking
6. **Extensibility**: Add new components or parameters without restructuring
7. **Integration**: Python can easily interact with both Terraform and Ansible
8. **Analysis**: Direct integration with data science tools for analyzing results

## Additional Features to Consider

1. **Results Database**: Store benchmark results in a structured database for easier analysis
2. **Visualization Dashboard**: Create a dashboard to visualize benchmark results in real-time
3. **Failure Recovery**: Implement checkpointing to resume interrupted experiments
4. **Parallel Execution**: Run multiple experiments in parallel if resources permit
5. **Resource Monitoring**: Integrate with monitoring tools to collect system metrics during benchmarks

This Python + Hydra approach provides a much more robust, flexible, and maintainable solution than shell scripts, especially for a research project with complex configuration requirements and multiple experimental parameters.


# Decoupling Infrastructure Provisioning from Scheduler Configuration

You've identified a key architectural challenge: separating infrastructure provisioning from scheduler configuration while maintaining the dependency relationship between them. Let me propose a revised approach that addresses this concern.

## Revised Architecture

```
Infrastructure Layer                    Configuration Layer
┌─────────────────────────┐            ┌─────────────────────────┐
│ Terraform               │            │ Ansible                 │
│                         │            │                         │
│ ┌─────────────────────┐ │            │ ┌─────────────────────┐ │
│ │ Cluster Topology A  │ │            │ │ SLURM Configuration │ │
│ │ - 1 head, 4 compute │ │            │ └─────────────────────┘ │
│ └─────────────────────┘ │            │                         │
│                         │            │ ┌─────────────────────┐ │
│ ┌─────────────────────┐ │            │ │ K8s+Volcano Config  │ │
│ │ Cluster Topology B  │ │────────────│ └─────────────────────┘ │
│ │ - 1 head, 8 compute │ │    │       │                         │
│ └─────────────────────┘ │    │       │ ┌─────────────────────┐ │
│                         │    └───────│ │ Flux Configuration  │ │
│ ┌─────────────────────┐ │            │ └─────────────────────┘ │
│ │ Cluster Topology C  │ │            │                         │
│ │ - 2 head, 16 compute│ │            │                         │
│ └─────────────────────┘ │            │                         │
└─────────────────────────┘            └─────────────────────────┘
```

## Implementation Strategy

### 1. Modular Terraform Structure

Create a modular Terraform structure that defines different cluster topologies independent of the scheduler:

```
terraform/
├── modules/
│   ├── cluster-topologies/
│   │   ├── small-cluster/     # 1 head, 4 compute
│   │   ├── medium-cluster/    # 1 head, 8 compute
│   │   └── large-cluster/     # 2 head, 16 compute
│   └── network/               # Network configuration
├── variables.tf
├── main.tf                    # Main orchestration
└── outputs.tf                 # Structured outputs for Ansible
```

### 2. Parameterized Ansible Roles

Create Ansible roles that adapt to the infrastructure topology:

```
ansible/
├── inventory/
│   └── terraform_inventory.py  # Dynamic inventory from Terraform
├── roles/
│   ├── slurm/
│   │   ├── defaults/main.yml   # Default parameters
│   │   ├── templates/          # Topology-aware templates
│   │   └── tasks/main.yml      # Adapts to cluster size
│   ├── kubernetes/
│   └── flux/
└── playbooks/
    ├── configure-slurm.yml
    ├── configure-kubernetes.yml
    └── configure-flux.yml
```

### 3. Terraform Output as Configuration Input

The key to this approach is using Terraform outputs to provide structured information about the infrastructure to Ansible:

```hcl
# terraform/outputs.tf
output "cluster_configuration" {
  value = {
    topology_name = var.selected_topology
    head_nodes    = module.selected_topology.head_nodes
    compute_nodes = module.selected_topology.compute_nodes
    network_info  = module.network.network_info
    total_cores   = module.selected_topology.total_cores
    total_memory  = module.selected_topology.total_memory
    # Additional metadata about the infrastructure
  }
}
```

### 4. Orchestration Scripts

Create scripts that allow you to mix and match topologies with schedulers:

```bash
#!/bin/bash
# deploy-environment.sh

# Parse arguments
TOPOLOGY=$1    # small, medium, large
SCHEDULER=$2   # slurm, kubernetes, flux

# 1. Provision infrastructure
echo "Provisioning $TOPOLOGY cluster..."
cd terraform
terraform init
terraform apply -var="selected_topology=$TOPOLOGY" -auto-approve

# 2. Generate inventory and configuration data
terraform output -json > ../ansible/inventory/terraform_output.json

# 3. Configure selected scheduler
echo "Configuring $SCHEDULER on $TOPOLOGY cluster..."
cd ../ansible
ansible-playbook -i inventory/terraform_inventory.py playbooks/configure-$SCHEDULER.yml
```

## Example Implementation

### Terraform Module for a Cluster Topology

```hcl
# terraform/modules/cluster-topologies/medium-cluster/main.tf

variable "base_image_id" {}
variable "network_id" {}

# Head node
resource "libvirt_domain" "head_node" {
  name   = "head-node"
  memory = "16384"
  vcpu   = 8

  cpu {
    mode = "host-passthrough"
  }

  # Disk, network, etc.
}

# Compute nodes
resource "libvirt_domain" "compute_nodes" {
  count  = 8
  name   = "compute-node-${count.index}"
  memory = "32768"
  vcpu   = 16

  cpu {
    mode = "host-passthrough"
  }

  # Disk, network, etc.
}

output "head_nodes" {
  value = [{
    name       = libvirt_domain.head_node.name
    ip_address = libvirt_domain.head_node.network_interface[0].addresses[0]
    vcpus      = libvirt_domain.head_node.vcpu
    memory     = libvirt_domain.head_node.memory
  }]
}

output "compute_nodes" {
  value = [for i, node in libvirt_domain.compute_nodes : {
    name       = node.name
    ip_address = node.network_interface[0].addresses[0]
    vcpus      = node.vcpu
    memory     = node.memory
  }]
}

output "total_cores" {
  value = libvirt_domain.head_node.vcpu + sum([for node in libvirt_domain.compute_nodes : node.vcpu])
}

output "total_memory" {
  value = libvirt_domain.head_node.memory + sum([for node in libvirt_domain.compute_nodes : node.memory])
}
```

### Ansible Role Adapting to Topology

```yaml
# ansible/roles/slurm/templates/slurm.conf.j2
# SLURM configuration generated for {{ cluster_info.topology_name }} topology

ClusterName={{ cluster_name }}
ControlMachine={{ cluster_info.head_nodes[0].name }}

# Node definitions
{% for head in cluster_info.head_nodes %}
NodeName={{ head.name }} CPUs={{ head.vcpus }} RealMemory={{ head.memory // 1024 }} State=UNKNOWN
{% endfor %}

{% for node in cluster_info.compute_nodes %}
NodeName={{ node.name }} CPUs={{ node.vcpus }} RealMemory={{ node.memory // 1024 }} State=UNKNOWN
{% endfor %}

# Partition definition
PartitionName=normal Default=YES Nodes={% for node in cluster_info.compute_nodes %}{{ node.name }}{% if not loop.last %},{% endif %}{% endfor %} State=UP
```

```yaml
# ansible/playbooks/configure-slurm.yml
---
- name: Load cluster information from Terraform
  hosts: localhost
  gather_facts: no
  tasks:
    - name: Parse Terraform output
      set_fact:
        cluster_info: "{{ lookup('file', 'inventory/terraform_output.json') | from_json }}"
      
- name: Configure SLURM head node
  hosts: head_nodes
  become: true
  vars:
    cluster_info: "{{ hostvars['localhost']['cluster_info'] }}"
  roles:
    - common
    - slurm/controller
    - monitoring

- name: Configure SLURM compute nodes
  hosts: compute_nodes
  become: true
  vars:
    cluster_info: "{{ hostvars['localhost']['cluster_info'] }}"
  roles:
    - common
    - slurm/compute
    - monitoring
```

## Matrix Testing Approach

This decoupled architecture allows you to create a matrix of tests:

```
┌─────────────────┬──────────┬────────────┬──────┐
│ Topology        │ SLURM    │ K8s+Volcano│ Flux │
├─────────────────┼──────────┼────────────┼──────┤
│ Small Cluster   │ Test 1   │ Test 2     │Test 3│
├─────────────────┼──────────┼────────────┼──────┤
│ Medium Cluster  │ Test 4   │ Test 5     │Test 6│
├─────────────────┼──────────┼────────────┼──────┤
│ Large Cluster   │ Test 7   │ Test 8     │Test 9│
└─────────────────┴──────────┴────────────┴──────┘
```

You can automate running all combinations with a script:

```bash
#!/bin/bash
# run-test-matrix.sh

TOPOLOGIES=("small" "medium" "large")
SCHEDULERS=("slurm" "kubernetes" "flux")

for topology in "${TOPOLOGIES[@]}"; do
  for scheduler in "${SCHEDULERS[@]}"; do
    echo "Testing $scheduler on $topology topology"
    
    # Deploy environment
    ./deploy-environment.sh $topology $scheduler
    
    # Run benchmarks
    ./run-benchmarks.sh $topology $scheduler
    
    # Collect results
    ./collect-results.sh $topology $scheduler
    
    # Tear down environment
    ./teardown-environment.sh
  done
done
```

## Benefits of This Approach

1. **True Separation of Concerns**: Infrastructure and configuration are separate but coordinated
2. **Reusability**: Topologies and scheduler configurations can be mixed and matched
3. **Consistency**: Each scheduler is configured optimally for each topology
4. **Automation**: The entire test matrix can be run automatically
5. **Extensibility**: New topologies or schedulers can be added independently

This architecture gives you the flexibility to test different combinations while ensuring that scheduler configurations properly adapt to the underlying infrastructure topology.