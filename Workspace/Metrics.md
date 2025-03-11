### Metrics

#### Resource Utilization
Resource utilization measures the extent to which available resources, such as bandwidth, memory, and GPU, are utilized by the scheduled workloads .... High resource utilization indicates efficient allocation, while low utilization may suggest underutilization or resource wastage

#### Fairness

Fairness metric assesses the equitable distribution of resources among different users or workloads . The objective is to prevent any single workload from monopolizing available resources to the detriment of others . For example, finish-time fairness measures the ratio of a workload’s completion time in a shared environment to its completion time if run alone, providing a measure of resource allocation equity ....

#### Job Completion time

Overall job completion time measures the total duration required to execute a task or workload across a system. This metric includes the time a job spends waiting (pending time), actively processing (running time), and concluding operations (destruction time) . This metric is particularly significant when jobs are distributed across multiple servers . Even if a task runs slower on an individual server, parallel processing on several servers can reduce the aggregate completion time, enhancing performance across the system ....

#### Elasticity

Elasticity measures the ability of the scheduler to handle increasing workload demands and scale resources accordingly . An elastic scheduler can manage resource allocation effectively even as workload size and complexity grow . It optimizes resource utilization by scaling resources up or down in response to workload changes, ensuring efficient operation even during peak usage periods .

### Extra

| Metric                        | Definition                           | Goal         |
| ----------------------------- | ------------------------------------ | ------------ |
| **Job Completion Time (JCT)** | Time taken for a job to complete     | Minimize     |
| **Fairness (JFI, Std Dev.)**  | Even resource allocation             | Maximize JFI |
| **Throughput**                | Jobs completed per unit time         | Maximize     |
| **Makespan**                  | Time to complete all jobs            | Minimize     |
| **Resource Utilization**      | Percentage of resource usage         | Maximize     |
| **Response Time**             | Time until a job starts execution    | Minimize     |
| **Waiting Time**              | Time spent in queue before execution | Minimize     |
| **Slowdown Factor**           | Ratio of JCT to execution time       | Minimize     |
| **Energy Efficiency**         | Jobs completed per unit of energy    | Maximize     |
