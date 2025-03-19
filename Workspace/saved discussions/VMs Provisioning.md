# Infrastructure as Code for HPC Scheduler Benchmarking

For your virtualized HPC scheduler benchmarking environment, I recommend a combination of tools that will provide automation, reproducibility, and flexibility. Here's a comprehensive approach:

## Recommended IaC Stack

### 1. Terraform + Libvirt Provider
**Primary VM provisioning and management**

```
Terraform (with libvirt provider)
├── VM Resource Definitions
│   ├── CPU/Memory/Storage allocation
│   ├── Network configuration
│   └── Boot images and initialization
└── Cluster Topology
    ├── Head/Master nodes
    └── Compute nodes
```

- **Advantages**: Declarative infrastructure definition, state management, reproducible deployments
- **Implementation**: Use the `terraform-provider-libvirt` to create and manage KVM VMs on your supercomputer node

### 2. Ansible for Configuration Management

```
Ansible Playbooks
├── Base System Configuration
│   ├── OS hardening
│   ├── Package installation
│   └── Network tuning
├── Scheduler-Specific Configuration
│   ├── SLURM Cluster Setup
│   ├── Kubernetes + Volcano Setup
│   └── Flux Framework Setup
└── Monitoring & Metrics Collection
    ├── Prometheus/Grafana deployment
    └── Custom metric collectors
```

- **Advantages**: Idempotent configuration, rich module library, easy to understand YAML syntax
- **Implementation**: Use Ansible to configure the VMs after Terraform provisions them

### 3. Packer for Base Image Creation

```
Packer Templates
├── Base OS Images
│   ├── Ubuntu/Rocky Linux optimized for HPC
│   └── Pre-installed dependencies
├── Scheduler-Specific Images
│   ├── SLURM-ready image
│   ├── Kubernetes-ready image
│   └── Flux-ready image
└── Build Configuration
    └── KVM/QEMU builder settings
```

- **Advantages**: Consistent base images, faster deployment, reduced configuration drift
- **Implementation**: Create optimized base images with necessary packages pre-installed

## Implementation Example

Here's a sketch of how your implementation might look:

### 1. Directory Structure

```
benchmark-infrastructure/
├── terraform/
│   ├── main.tf                 # Main Terraform configuration
│   ├── variables.tf            # Variable definitions
│   ├── slurm-cluster.tf        # SLURM cluster definition
│   ├── kubernetes-cluster.tf   # Kubernetes cluster definition
│   ├── flux-cluster.tf         # Flux cluster definition
│   └── outputs.tf              # Output definitions
├── ansible/
│   ├── inventory/              # Dynamic inventory from Terraform
│   ├── roles/
│   │   ├── common/             # Common configuration for all nodes
│   │   ├── slurm/              # SLURM-specific configuration
│   │   ├── kubernetes/         # Kubernetes-specific configuration
│   │   ├── flux/               # Flux-specific configuration
│   │   └── monitoring/         # Monitoring tools configuration
│   └── playbooks/
│       ├── setup-slurm.yml
│       ├── setup-kubernetes.yml
│       └── setup-flux.yml
├── packer/
│   ├── base-image.json         # Base image configuration
│   ├── slurm-image.json        # SLURM-specific image
│   ├── kubernetes-image.json   # Kubernetes-specific image
│   └── flux-image.json         # Flux-specific image
└── scripts/
    ├── deploy.sh               # Main deployment script
    ├── benchmark.sh            # Benchmark execution script
    └── collect-metrics.sh      # Metrics collection script
```

### 2. Sample Terraform Configuration (main.tf)

```hcl
terraform {
  required_providers {
    libvirt = {
      source = "dmacvicar/libvirt"
    }
  }
}

provider "libvirt" {
  uri = "qemu:///system"
}

# Define a base volume from a cloud image
resource "libvirt_volume" "base_volume" {
  name   = "base-volume"
  source = var.base_image_path
}

# Network for the VMs
resource "libvirt_network" "benchmark_network" {
  name      = "benchmark-network"
  mode      = "nat"
  domain    = "benchmark.local"
  addresses = ["10.0.100.0/24"]
}

# Include scheduler-specific configurations
module "slurm_cluster" {
  source = "./modules/slurm"
  
  base_volume_id = libvirt_volume.base_volume.id
  network_id     = libvirt_network.benchmark_network.id
  node_count     = var.compute_node_count
  cpu_count      = var.cpu_per_node
  memory_size    = var.memory_per_node
}

# Similar modules for Kubernetes and Flux
```

### 3. Sample Ansible Playbook (setup-slurm.yml)

```yaml
---
- name: Configure SLURM head node
  hosts: slurm_head
  become: true
  roles:
    - common
    - slurm/head
    - monitoring

- name: Configure SLURM compute nodes
  hosts: slurm_compute
  become: true
  roles:
    - common
    - slurm/compute
    - monitoring
```

### 4. Integration Script (deploy.sh)

```bash
#!/bin/bash
set -e

# Build base images if needed
if [ "$BUILD_IMAGES" = "true" ]; then
  echo "Building base images with Packer..."
  packer build packer/base-image.json
fi

# Deploy infrastructure with Terraform
echo "Deploying virtual infrastructure..."
cd terraform
terraform init
terraform apply -auto-approve

# Generate Ansible inventory
terraform output -json | jq -r '.ansible_inventory.value' > ../ansible/inventory/hosts

# Configure clusters with Ansible
cd ../ansible
ansible-playbook -i inventory/hosts playbooks/setup-slurm.yml
ansible-playbook -i inventory/hosts playbooks/setup-kubernetes.yml
ansible-playbook -i inventory/hosts playbooks/setup-flux.yml

echo "Infrastructure deployment complete!"
```

## Performance Optimization Considerations

For accurate benchmarking, include these optimizations:

1. **CPU Pinning**: Pin VM vCPUs to physical cores to prevent migration
   ```hcl
   # In Terraform libvirt configuration
   cpu {
     mode = "host-passthrough"
   }
   ```

2. **NUMA Awareness**: Configure VMs to respect NUMA topology
   ```hcl
   # In Terraform libvirt configuration
   numa_mode = "strict"
   ```

3. **Memory Configuration**: Use hugepages for better performance
   ```hcl
   # In Terraform libvirt configuration
   memory {
     hugepages = true
   }
   ```

4. **Network Optimization**: Configure SR-IOV or PCI passthrough if available

## Conclusion

This Infrastructure as Code approach provides:

1. **Reproducibility**: The entire environment can be recreated consistently
2. **Automation**: Minimal manual intervention required
3. **Scalability**: Easy to adjust parameters for different test scenarios
4. **Documentation**: The code itself documents the environment
5. **Version Control**: Track changes to your infrastructure over time

For your specific use case of benchmarking HPC schedulers, this approach allows you to create isolated, consistent environments for each scheduler while maximizing the accuracy of your benchmarks.