
Ideas

- Kubernetes Scheduler (MSE paper benchmark)
- Heterogen load on slurm clusters (LLM vs classic HPC =>what scheduler ?)
- Scheduler on disaggregated memory (lbnl paper)
- Explore and benchmark solutions like (disco, ray, run.ai)
- Generally : How to accelerate AI Computing in HPC clusters with software stack

---

## Simulator

Inputs:

- Job trace (job id, n nodes, runtime requested)
- Node trace (memory, actual runtime)

Try to emulate the scheduler

job has requirements:

- CPU
- GPU
- Memory
- Memory bandwith

Resources:
- CPUS
- GPUs
- Memory

for the os, the memory is the max over the job lifetime.

Key = jobID


===


Graph matching optimization => Linear programming Bipartite graph Maximum Bipartite Graph

FM got the equation

Augmenting path (Decentralized)

=>
Perspective:

Oracle first (Centralized version)
part of system


===

they do have a premium queue and a regular queue.
All the jobs have a priority number ( priority is updated regulary)
We want to give prirority in the node that waited longer ( time in the waiting line, money)

===

Separable allocators: two variance

Requestor ask for resources

Resources has inner decision capabilities.

They communicate the decisions and the loop will go one until everyone has a resources assigned.


They loadbalance the request =>

---

## Simulator Onboarding

Follow Readme instruction and run some test. 
1) get good job traces
2) Batch jobs in the HPC systems (Reduce time)
3) Run Tests => new ideas => change the code of the simulation

Less than 30 min

They didn't considered the GPU.

