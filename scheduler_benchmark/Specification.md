# Benchmark Specification: Multi-Objective Comparison of HPC Schedulers

## Problem Definition

This project aims to benchmark and compare multiple HPC schedulers—such as SLURM, Kubernetes (with Volcano or other schedulers), and Flux—across different hardware and software environments. The ultimate goal is to determine which scheduler configurations are best suited for various workload categories found in high-performance computing (HPC) clusters, while considering multiple competing metrics in a Pareto optimization framework.

## Pareto Definition

Pareto optimization with multiple metrics addresses the challenge of optimizing several competing objectives without a clear hierarchy among them. Instead of finding one “best” solution, we seek to identify a set of solutions (the Pareto frontier) where improving one metric necessarily degrades at least one other. In the context of cluster scheduling, we balance throughput, latency, energy consumption, and other metrics, recognizing that different workloads may prioritize different objectives.

## Metric Definition

The following metrics will be used to evaluate the schedulers:

1. **Resource Utilization**  
   - Measures the extent to which available resources (e.g., CPU, memory, GPU, network bandwidth) are employed.  
   - Higher utilization indicates more efficient use of resources, while underutilization suggests waste.

2. **Fairness**  
   - Assesses the equitable distribution of resources among users or workloads.  
   - Finish-time fairness, for instance, compares completion time in a shared environment versus alone, ensuring no single workload monopolizes resources.

3. **Job Completion Time**  
   - Encompasses the entire duration required for a job to finish—queueing, execution, and teardown.  
   - Particularly important in multi-node HPC environments, where parallel processing can drastically reduce total completion time.

4. **Elasticity**
   - Evaluates how well the scheduler can adapt to fluctuating workloads by scaling resources up or down.  
   - Efficient elasticity ensures workload demands are met while preventing resource bottlenecks or waste.

## Research Question

1. How do different cluster schedulers (e.g., SLURM, Kubernetes+Volcano, Flux) perform under varying workload characteristics and heterogeneous hardware configurations?​
2. What trade-offs exist between throughput, fairness, job completion time, and elasticity in different scheduling approaches?​
3. How can Pareto-optimal configurations be identified to optimize scheduling performance across diverse workloads?

## Methodology

1. **Workload Analysis & Creation**  
   - Extract job traces from Perlmutter.  
   - Identify representative workload classes (e.g., short CPU-bound jobs, GPU-heavy jobs, data-intensive analytics, multi-node MPI jobs, etc.).  
   - Create containerized workloads (using Singularity/Apptainer or Docker) to model these categories.

2. **Environment Deployment**  
   - Use virtual machines to provision the test cluster.
   - Configure each environment to match specific hardware profiles (1,2,4,8 cpus, 1,2,4,8 gpus, 4,8,16,32 Gb Ram, etc...).
   - Install the chosen schedulers (SLURM, Kubernetes+Volcano, Flux, etc.).  

3. **Execution & Metrics Collection**  
   - Run the suite of workloads on each scheduler and each hardware configuration.  
   - Collect data for resource utilization, fairness, job completion time, and elasticity.  
   - Utilize logging, monitoring, and monitoring tools to capture detailed performance metrics.

4. **Pareto Analysis**  
   - For each scheduler–environment combination, plot performance across multiple metrics in a Pareto frontier representation.  
   - Identify trade-offs (e.g., improved throughput vs. potentially reduced fairness).
   - Compare scheduling strategies and highlight performance bottlenecks or advantages.  
   - Provide guidelines on choosing the best scheduler for specific workload types and hardware configurations.

## Test Environment

```
Supercomputer Nodes
└── Virtualization Layer (KVM/QEMU)
    ├── VM Cluster 1: SLURM
    │   └── Containerized Workloads
    ├── VM Cluster 2: Kubernetes+Volcano
    │   └── Containerized Workloads
    └── VM Cluster 3: Flux Framework
        └── Containerized Workloads
```

## Machine

### CPU Nodes

![Perlmutter CPU nodes](https://docs.nersc.gov/systems/perlmutter/images/perlmutter_cpu_node.png)

- 2x [AMD EPYC 7763](https://www.amd.com/en/products/cpu/amd-epyc-7763) (Milan) CPUs
- 64 cores per CPU
- AVX2 instruction set
- 512 GB of DDR4 memory total
- 204.8 GB/s memory bandwidth per CPU
- 1x [HPE Slingshot 11](https://www.hpe.com/us/en/compute/hpc/slingshot-interconnect.html) NIC
- PCIe 4.0 NIC-CPU connection
- 39.2 GFlops per core
- 2.51 TFlops per socket
- 4 NUMA domains per socket (NPS=4)

## Infrastructure provisioning

This section details the infrastructure provisioning component of the HPC scheduler benchmarking framework. The infrastructure layer is responsible for creating virtualized environments that simulate various cluster topologies on which different schedulers will be tested. The provisioning process is designed to be fully automated, reproducible, and configurable to support the multi-objective comparison of HPC schedulers.

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
└───────────────────────┘  └─────────────────────────┘

### requirements

#### functional requirements

- Automated Provisioning: The system must be able to automatically provision virtual clusters with different topologies without manual intervention.
- Topology Flexibility: Support for multiple predefined cluster topologies (small, medium, large) with varying numbers of head and compute nodes.
- Resource Configuration: Ability to specify CPU, memory, disk, and network configurations for each node type.
- Network Configuration: Creation of isolated networks for each cluster with appropriate routing and DNS.
- Idempotency: Ensure provisioning operations are idempotent to support retries and incremental changes.
- Cleanup: Provide mechanisms to completely tear down provisioned resources after experiments.
- Speed: Intermediate images should be used to speed up the provisioning process, allowing for quick reconfiguration and testing of different setups.

#### non-functional requirements

Reliability: The provisioning process should be robust against transient failures.
Observability: Provide detailed logging and status information during the provisioning process.

### Architecture

The infrastructure provisioning component follows a layered architecture:

Configuration Layer: Hydra-based configuration system for defining infrastructure parameters
Orchestration Layer: Python modules that interpret configurations and manage the provisioning workflow
Provisioning Layer: Terraform modules that handle the actual resource creation
Resource Layer: The virtualized infrastructure created on the target platform

#### Configuration System

The infrastructure configuration uses Hydra to manage complex, hierarchical configurations:

```txt
conf/
├── config.yaml                # Base configuration
└── topology/                  # Infrastructure topologies
    ├── small.yaml             # 1 head node, 4 compute nodes
    ├── medium.yaml            # 1 head node, 8 compute nodes
    └── large.yaml             # 2 head nodes, 16 compute nodes
```

Each topology configuration specifies:

Number and type of head nodes
Number and type of compute nodes
Network configuration
Storage configuration
Resource allocations (CPU, memory, disk)
Example topology configuration:

#### Terraform Infrastructure

The Terraform code is organized into modules for reusability and maintainability:

```python
terraform/
├── main.tf                    # Main orchestration
├── variables.tf               # Input variables
├── outputs.tf                 # Output definitions
└── modules/
    ├── network/               # Network configuration
    ├── storage/               # Storage configuration
    ├── head_node/             # Head node provisioning
    ├── compute_node/          # Compute node provisioning
    └── monitoring/            # Monitoring infrastructure
```

The Terraform configuration receives parameters from the Python orchestration layer, which translates Hydra configurations into Terraform variables.

#### Provisioning Workflow

The infrastructure provisioning process follows these steps:

Initialization: Parse and validate the selected topology configuration
Resource Planning: Determine the resources needed and verify availability
Network Creation: Set up isolated networks for the cluster
Storage Provisioning: Create shared storage systems
Head Node Deployment: Provision and configure head node(s)
Compute Node Deployment: Provision and configure compute nodes
Verification: Validate that all resources are correctly provisioned
Output Generation: Generate structured output for the configuration phase
