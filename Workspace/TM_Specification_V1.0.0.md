
# Master's Work Specification: Online Distributed Maximum Bipartite Matching for Disaggregated Computing Schedulers

## 1. Problem Definition

In large-scale computing environments, particularly in disaggregated computing clusters, the efficient assignment of computational jobs to available resources is critical. Traditional monolithic architectures couple memory, CPU, and accelerators into fixed nodes, leading to inefficient resource utilization. Disaggregated computing decouples these resources, enabling more flexible and efficient scheduling. However, online job scheduling remains a significant challenge, as jobs arrive dynamically, and resource states evolve continuously.

This work aims to study and develop scheduling algorithms for online distributed maximum bipartite matching, ensuring fair, efficient, and scalable job placement. Specifically, the problem can be formulated as an online bipartite matching problem, where:

- Jobs (U) arrive dynamically and must be matched to resources (V).
- Each job reveals its constraints (e.g., CPU, memory, GPU, network bandwidth) only upon arrival.
- Once a job is assigned, the decision is irrevocable.
- The objective is to maximize resource utilization, fairness, and overall system performance.

This problem has direct applications in high-performance computing (HPC) schedulers, cloud computing, and modern Kubernetes-based cluster management.

---

## 2. Research Framework

This study is framed within the field of high-performance computing (HPC) and scheduling algorithms. The following key areas define the scope:

- Online Bipartite Matching Theory: Extending classical approaches such as the Ranking Algorithm (achieving a competitive ratio of \(1 - 1/e\)) to distributed environments.
- Disaggregated Computing: Analyzing how decoupled memory, CPUs, and GPUs affect job scheduling, performance trade-offs, and algorithmic design.
- Scheduling Policies in HPC: Investigating existing schedulers in Kubernetes and HPC environments, particularly those optimized for dynamic, heterogeneous workloads.

---

## 3. Disaggregated Computing and Its Advantages

Disaggregated computing introduces the following advantages:

1. Improved Resource Utilization: Memory and computing power can be shared dynamically across workloads.
2. Flexibility in Resource Allocation: Jobs can be scheduled based on real-time availability rather than static node allocation.
3. Better Adaptability to Workload Variability: Reduces idle resources by allowing fine-grained scaling of compute and memory.
4. Cost Efficiency: Reduces overall infrastructure costs by eliminating resource fragmentation.

However, increased scheduling complexity arises due to:

- Higher network latency for remote memory access.
- Non-uniform memory access (NUMA) performance variations.
- Challenges in fair and efficient job scheduling across a dynamic pool of resources.

These trade-offs must be incorporated into the scheduler design.

---

## 4. Performance Metrics

The evaluation of scheduling algorithms will be based on several metrics, commonly used in Kubernetes schedulers and HPC job scheduling:

1. Resource Utilization: The ratio of allocated vs. idle CPU, GPU, and memory resources.
2. Fairness: How equitably resources are distributed among jobs.
3. Job Slowdown: The bounded slowdown metric, defined as:

   \[
   \text{bsld}_i = \max\left( \frac{w_i + d_i}{\max(d_i, \tau)}, 1 \right)
   \]

   where \( w_i \) is waiting time, \( d_i \) is execution time, and \( \tau \) is a small threshold to normalize short jobs.

4. Throughput: Number of jobs completed per unit time.
5. Compute Node Utilization: Fraction of time compute nodes are active.
6. Matching Efficiency: Percentage of jobs assigned to optimal resources.
7. Latency Overhead: Additional delays introduced by disaggregated resource allocation.

These metrics will be visualized using Pareto frontiers, enabling comparisons of different scheduling strategies.

---

## 5. Methodology

This project follows a structured research approach:

### Step 1: Define the Algorithmic Landscape

- Review existing online bipartite matching algorithms (e.g., Ranking, Greedy, Learning-based Approaches).
- Investigate state-of-the-art HPC job schedulers in Kubernetes and Slurm.
- Identify gaps in distributed scheduling algorithms for disaggregated computing.

### Step 2: Document Existing Approaches

- Compile research papers on scheduling in HPC and Kubernetes.
- Compare fairness, performance trade-offs, and scalability of existing scheduling strategies.

### Step 3: Simulator Setup

- Select or develop a simulation framework for evaluating scheduler performance.
- Configure workload models based on real-world HPC job traces.

### Step 4: Define and Validate Metrics

- Implement bounded slowdown, fairness, and utilization metrics.
- Cross-validate with existing Kubernetes scheduling benchmarks.

### Step 5: Implement and Test Different Scheduling Approaches

- Implement baseline algorithms (e.g., Greedy, FCFS, Backfilling).
- Design adaptive scheduling techniques for disaggregated environments.
- Experiment with multi-objective optimization for trade-offs between fairness and utilization.

### Step 6: Iteration and New Approaches

- Analyze limitations of initial results.
- Develop hybrid or reinforcement learning-based scheduling policies.
- Optimize algorithms based on latency-aware placement strategies.

### Step 7: Write Final Report

- Document methodology, findings, and performance comparisons.
- Propose recommendations for future scheduler implementations.

---

## 6. Additional Considerations

- Comparison with Kubernetes schedulers: How does the proposed scheduler compare to Kubernetes-native scheduling frameworks such as KubeShare, Gandiva, and SchedTune?
- Network Overhead: Evaluating the impact of increased network communication when matching jobs to resources across racks.
- Scalability: Testing how the scheduler performs under increasing system loads.

---

## Conclusion

This research seeks to advance the field of disaggregated computing job scheduling by designing and evaluating online distributed maximum bipartite matching algorithms. The study will provide quantitative insights into fairness, utilization, and efficiency trade-offs, ultimately guiding future HPC scheduler designs.

---

### Next Steps

- Finalize the list of algorithms to be implemented.
- Choose an HPC simulation framework for experiments.
- Define a baseline scheduler to compare against.
- Start implementing the evaluation environment.
