I'm conducting research to benchmark different HPC schedulers (SLURM, Kubernetes+Volcano, Flux) across various workload patterns. I need comprehensive Perlmutter usage data to identify representative workload categories and their resource utilization patterns for creating realistic test scenarios.

Timeframe

- Period: > 2 months, as much as possible
- Sampling rate: 10-second intervals (as configured in LDMS/DCGM) ?

 Job Metadata

- Job ID, user/group ID
- Submission time, start time, end time
- Allocated resources (nodes, cores, GPUs, memory)
- Requested walltime vs. actual runtime
- Queue/partition information
- Exit status (success/failure)
- Dependencies and job arrays information

Node-Level Metrics

CPU utilization:
    - Per-node CPU utilization percentages
    - Core-level utilization if available
 Memory usage:
    - Host DRAM utilization (used/total)
    - Memory bandwidth if available
I/O operations:
    - Storage read/write operations
    - I/O bandwidth utilization
Network metrics:
    - Interconnect traffic patterns
    - Communication volume between nodes

GPU-Specific Metrics (for GPU nodes)

- GPU utilization: SM utilization percentage
- GPU memory: HBM2 memory usage
- NVLink traffic: Inter-GPU communication patterns
- GPU kernel statistics: If available, counts of kernel launches
- GPU power consumption: If available

Scheduler-Related Metrics

- Queue wait times
- Job priority information
- Backfill statistics
- Resource fragmentation data

## Additional Requests

- Documentation on metric collection methodology
- Information on system configuration during the collection period
- Any known system maintenance events that might have affected workloads

This data will enable me to understand the resource utilization imbalances (both temporal and spatial) across different workload types, which is crucial for creating realistic benchmarks and comparing scheduler performance across multiple objectives including resource utilization, fairness, job completion time, and elasticity.