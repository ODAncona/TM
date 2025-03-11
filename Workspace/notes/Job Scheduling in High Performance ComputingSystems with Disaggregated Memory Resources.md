Reason:

- Improve system resource utilization

## Background

**Memory Disaggregation System Architectures:**
- Traditional systems allocate CPUs, GPUs, and memory in node units to jobs.
- Disaggregated memory systems introduce shared memory pools for job allocation.


Optimization metrics of the job scheduler.

Fair Memory (FM): scheduling algorithm.

## Summary
This research focuses on addressing the memory demands of applications in high-performance computing (HPC) systems through the use of disaggregated memory resources. By introducing memory pools that can be shared among jobs, the study proposes a data-driven approach to evaluate job scheduling and resource allocation in these systems. The paper introduces a novel job scheduling algorithm, FM (Fair Memory), that considers both local and disaggregated memory resources to enhance system efficiency. Simulation results demonstrate that FM outperforms traditional schedulers in terms of job slowdown and fairness, particularly when shared memory pool capacity is limited, showcasing its effectiveness in optimizing job scheduling in HPC environments.


 idle resources couldn't be leveraged due to static configurations
 Node sharing for jobs was limited and didn't fully address resource waste, especially given the diverse memory requirements of HPC applications


Disaggregated memory, termed remote memory, enables finer resource allocation to match application needs precisely.

## Challenges
- Varied memory access latency
- Increased network load
- Complex task of balancing local and remote memory allocation to optimize multiple parameters

## Metrics

- physical location of memory modules
- Interference issues

## Questions

- Should job schedulers account for the location and constraints of remote memory resources in addition to existing considerations?
- How should the local and remote memory pool capacities ratio be determined to minimize performance impact and system memory usage?
- What benefits does disaggregated memory offer HPC systems?
## Contributions

- Introducing an application performance model to quantify additional latency when accessing remote memory and estimating job performance in a memory-disaggregated system.
- Simulation of HPC systems with disaggregated memory using traces from two production systems to assess system and job performance across different memory configurations.
- Presenting throughput per dollar spent on memory resources as a measure of cost-effectiveness for disaggregated memory systems and determining optimal memory per rack for the two production systems.