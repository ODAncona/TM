# Characteristics of Job Traces

In our study, we collected real job traces from the CPU nodes in NERSC’s Perlmutter (referred to as the Perlmutter trace) and the GPU nodes in the JUWELS Booster Module at Julich Supercomputing Centre (referred to as the JUWELS trace). These job traces were collected from SLURM and include actual memory usage metrics obtained from LDMS on Perlmutter and LLview , on JUWELS. The job traces contain the following fields:

1) Submit Time: This refers to the timestamp when a job
enters the system queue. We preserve this field to reflect
the real submission pattern observed in HPC systems.
2) Duration: This is the time it takes a job to complete
once it starts executing. We utilize the aforementioned
performance degradation model to adjust the job’s duration
based on the memory type (local or remote) it is allocated
and the capacity of each type.
3) Number of Nodes: This is the number of nodes exclusively
allocated to a job. We concentrate on node allocation
instead of processor allocation as neither Perlmutter nor
JUWELS currently allow sharing nodes between jobs.
Thus, nodes are exclusively used by one job.
4) Maximum Memory Used: This denotes the maximum
memory used per node across all nodes allocated to a
job. We record the peak memory usage through LDMS or
LLview to accurately reflect the real maximum memory
requirements of jobs.

# Data Description

NERSC collects system-wide monitoring data through the Lightweight Distributed Metric Service (LDMS) and Nvidia’s Data Center GPU Manager (DCGM). LDMS is deployed on both CPU-only and GPU nodes; it samples node-level metrics either from a subset of hardware performance counters or operating system data, such as memory usage, I/O operations, etc. DCGM is dedicated to collecting GPU-specific metrics, including GPU utilization, GPU memory utilization, NVlink traffic, etc. The sampling interval of both LDMS and DCGM is set by the system at 10 s. The monitoring data are aggregated into CSV files from which we build a processing pipeline for our analysis, shown in Fig. 1. As a last step, we merge the job metadata from SLURM (job ID, job step, allocated nodes, start time, end time, etc.) with the node-level monitoring metrics. The output from our flow is a set of parquet files. Due to the large volume of data, we only sample Perlmutter from November 1 to December 1 of 2022. The system’s monitoring infrastructure is still under deployment and some important traces such as memory bandwidth are not available at this time.

We measure CPU utilization from `cpu id` (CPU idle time among all cores in a node, expressed as a percentage) reported from `vmstat` through LDMS; we then calculate CPU utilization (as a percentage) as: `100 − cpu id`. GPU utilization (as a percentage) is directly read from DCGM reports. Memory capacity utilization encompasses both the utilization of memory by user-space applications and the operating system. We use `fb free` (framebuffer memory free) from DCGM to calculate GPU HBM2 utilization and `mem free` (the amount of idle memory) from LDMS to calculate host DRAM capacity utilization. Memory capacity utilization (as a percentage) is calculated as:

$$
MemUtil = \frac{MemTotal - MemFree}{MemTotal} \times 100
$$

where `MemTotal`, as described above, is 512 GB for CPU nodes, 256 GB for the host memory of GPU nodes, and 40 GB for each GPU HBM2. `MemFree` is the unused memory of a node, which essentially shows how much more memory the job could have used.

In order to understand the temporal and spatial imbalance of resource usage among jobs, we use the equations proposed in to calculate the temporal imbalance factor (`RItemporal`) and spatial imbalance factor (`RIspatial`). These factors allow us to quantify the imbalance in resource usage over time and across nodes, respectively. For a job that requests N nodes and runs for time T, and its utilization of resource r on node n at time t is `U_{n,t}`, the temporal imbalance factor is defined as:

$$
RItemporal(r) = \max_{1 \le n \le N} \left(1 - \frac{\sum_{t=0}^{T} U_{n,t}}{\sum_{t=0}^{T} \max_{0 \le t \le T} (U_{n,t})}\right)
$$

Similarly, the spatial imbalance factor is defined as:

$$
RIspatial(r) = 1 - \frac{\sum_{n=1}^{N} \max_{0 \le t \le T} (U_{n,t})}{\sum_{n=1}^{N} \max_{0 \le t \le T, 1 \le n \le N} (U_{n,t})}
$$

Both `RItemporal` and `RIspatial` are bound within the range of [0, 1]. Ideally, a job uses fully all resources on all allocated nodes across the job’s lifetime, corresponding to a spatial and temporal factor of 0. A larger factor value indicates a variation in resource utilization temporally/spatially and the job experiences more temporal/spatial imbalance.

We exclude jobs with a runtime of less than 1 hour in our subsequent analysis, as such jobs are likely for testing or debugging purposes. Furthermore, since our sampling frequency is 10 seconds, it is difficult to capture peaks that last less than 10 seconds accurately. As a result, we concentrate on analyzing the behavior of sustained workloads. Table 1 summarizes job-level statistics in which each job’s resource usage is represented by its maximum resource usage among all allocated nodes throughout its runtime.
