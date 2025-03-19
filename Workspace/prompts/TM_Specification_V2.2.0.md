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

1. **Elasticity**
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
   - Define which environment to use (bare metal, LXC/LXD, virtual machines) to provision the test cluster.
   -  Configure each environment to match specific hardware profiles (1,2,4,8 cpus, 1,2,4,8 gpus, 4,8,16,32 Gb Ram, etc...).
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