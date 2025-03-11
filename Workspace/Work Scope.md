
## Pareto Optimization

Pareto optimization with multiple metrics addresses the challenge of simultaneously optimizing several competing objectives without a clear hierarchy among them. In multiple objective optimization, rather than seeking a single "best" solution, the goal is to identify a set of solutions known as the Pareto frontier—where improving one metric necessarily degrades at least one other metric. These solutions represent optimal trade-offs where no objective can be improved without sacrificing performance in another dimension. For example, in cluster scheduling, one might balance throughput, latency, and energy consumption, with each point on the Pareto frontier representing a different but equally valid prioritization of these metrics.

### Metrics

#### Resource Utilization
Resource utilization measures the extent to which available resources, such as bandwidth, memory, and GPU, are utilized by the scheduled workloads .... High resource utilization indicates efficient allocation, while low utilization may suggest underutilization or resource wastage

#### Fairness

Fairness metric assesses the equitable distribution of resources among different users or workloads . The objective is to prevent any single workload from monopolizing available resources to the detriment of others . For example, finish-time fairness measures the ratio of a workload’s completion time in a shared environment to its completion time if run alone, providing a measure of resource allocation equity ....

#### Job Completion time

Overall job completion time measures the total duration required to execute a task or workload across a system. This metric includes the time a job spends waiting (pending time), actively processing (running time), and concluding operations (destruction time) . This metric is particularly significant when jobs are distributed across multiple servers . Even if a task runs slower on an individual server, parallel processing on several servers can reduce the aggregate completion time, enhancing performance across the system ....

#### Elasticity

Elasticity measures the ability of the scheduler to handle increasing workload demands and scale resources accordingly . An elastic scheduler can manage resource allocation effectively even as workload size and complexity grow . It optimizes resource utilization by scaling resources up or down in response to workload changes, ensuring efficient operation even during peak usage periods .


## Disaggregated Computing

Disaggregated computing separates memory resource allocation from compute resources, enabling more flexible and finer-grained memory allocation. Its scope includes granular resource allocation to meet specific application needs and improved resource utilization in high-performance computing (HPC) systems. It addresses the underutilization of expensive resources due to static allocation in traditional HPC systems. Potential benefits include better adaptation to growing memory demands and greater system efficiency. Challenges include increased memory access latency increased network pressure, and complexity in allocating local and remote resources to balance various objectives. Trade-offs involve juggling application runtime, costs, memory utilization, and job queuing time, as well as potential latency and bandwidth issues from remote memory.


## Cluster Management (What system for which usage)

When operating a computing cluster, the diversity of workloads—ranging from deep learning training to real-time inference, simulations, or data processing—presents a critical challenge: selecting the right orchestration system for the task. Each workload type has distinct demands, such as compute intensity, latency sensitivity, or scalability requirements, which influence the choice of tools. The key paradigm is aligning the system’s capabilities with the workload’s needs, balancing efficiency, resource utilization, and performance. This decision is not one-size-fits-all; it requires understanding whether the workload prioritizes batch processing, real-time responses, or dynamic scaling, and whether the tool can adapt to these demands without introducing unnecessary complexity or overhead. The stakes are high: mismatched systems risk underperformance, inefficiency, or even failure to meet operational goals.

---

I'm starting a project composed of 3 members and have three main direction:
1. First stakeholder want to do benchmark of scheduler with Pareto Optimization
2. Second Stakeholder want to publish a paper on the field Disaggregated Computing
3. Last stakeholder want to learn how to better Cluster Management
   
I need to find a three research questions that include these 3 directions.