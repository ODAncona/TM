
# Online Decentralized Maximum Bipartite Matching for Job Allocation

We define the problem in a rigorous mathematical framework. Consider a bipartite graph

$$
G = (V_1 \cup V_2, E)
$$

where:
- \( V_1 \) is the set of jobs.
- \( V_2 \) is the set of resources.
- \( E \) is the set of edges connecting jobs to resources. An edge \( (j, r) \in E \) indicates that resource \( r \) can serve job \( j \) (subject to resource capacity constraints).

## 1. Job and Resource Characteristics

### Jobs
For each job \( j \in V_1 \):
- **Arrival Time:** \( a_j \) (jobs arrive online, i.e., over time).
- **Processing Time:** \( p_j \).
- **Resource Requirement:** A vector \( \mathbf{r}_j \) representing the required amounts of different resources (e.g., memory, GPU, CPU).

### Resources
For each resource \( r \in V_2 \):
- **Capacity:** A vector \( \mathbf{c}_r \) representing the available amounts of different resource types.

An edge \( (j, r) \in E \) exists if
$$
\mathbf{r}_j \le \mathbf{c}_r \quad \text{(component-wise).}
$$

## 2. Decision Variables and Matching Constraints

Define the binary decision variable:
$$
x_{jr} = \begin{cases}
1, & \text{if job } j \text{ is assigned to resource } r, \\
0, & \text{otherwise.}
\end{cases}
$$

The matching is subject to the following constraints:

- **Job Constraint:** Each job is assigned to at most one resource:
$$
\sum_{r:\, (j,r) \in E} x_{jr} \leq 1, \quad \forall\, j \in V_1.
$$

- **Resource Constraint:** Each resource can process at most one job at a time:
$$
\sum_{j:\, (j,r) \in E} x_{jr} \leq 1, \quad \forall\, r \in V_2.
$$

## 3. Online and Decentralized Aspects

- **Online Setting:**  
  Jobs arrive progressively. At any time \( t \), only the jobs with \( a_j \le t \) are known. The decision \( x_{jr} \) for a job \( j \) must be made at (or shortly after) its arrival, without knowledge of future jobs.

- **Decentralized Setting:**  
  The scheduling system is partitioned among multiple schedulers. Let:
  - \( \mathcal{S} \) be the set of schedulers.
  - Each scheduler \( s \in \mathcal{S} \) has access to a local subset \( V_1^s \subset V_1 \) of jobs and \( V_2^s \subset V_2 \) of resources.

  Decisions are made based on local, partial information, with coordination protocols ensuring global consistency and non-conflicting assignments.

## 4. Multi-Objective (Pareto) Optimization

The objective is to optimize several performance metrics simultaneously. Let the performance vector be:
$$
F(x) = \big( f_1(x), f_2(x), \dots, f_k(x) \big)
$$
where the metrics include:

| **Metric**                     | **Definition**                                | **Goal**       |
|--------------------------------|-----------------------------------------------|----------------|
| **Job Completion Time (JCT)**  | Time taken for a job to complete              | Minimize       |
| **Fairness (JFI, Std Dev.)**   | Even resource allocation (JFI)                | Maximize JFI   |
| **Throughput**                 | Jobs completed per unit time                  | Maximize       |
| **Makespan**                   | Time to complete all jobs                     | Minimize       |
| **Resource Utilization**       | Percentage of resource usage                  | Maximize       |
| **Response Time**              | Time until a job starts execution             | Minimize       |
| **Waiting Time**               | Time spent in queue before execution          | Minimize       |
| **Slowdown Factor**            | Ratio of JCT to execution time                | Minimize       |
| **Energy Efficiency**          | Jobs completed per unit of energy             | Maximize       |

Since these objectives can conflict, the goal is to obtain a **Pareto optimal** solution. A matching \( x^* \) is Pareto optimal if there is no other feasible matching \( x \) such that:
- For every metric \( i \) to be minimized: \( f_i(x) \le f_i(x^*) \),
- For every metric \( j \) to be maximized: \( f_j(x) \ge f_j(x^*) \),
with at least one inequality being strict.

Alternatively, all objectives can be transformed into a minimization (or maximization) problem by, for example, taking the negative of maximization metrics.

## 5. Overall Problem Statement

**Objective:** Find an assignment \( x \in \{0,1\}^{|E|} \) that satisfies:
$$
\begin{aligned}
& \sum_{r:\, (j,r) \in E} x_{jr} \leq 1, \quad \forall\, j \in V_1, \\
& \sum_{j:\, (j,r) \in E} x_{jr} \leq 1, \quad \forall\, r \in V_2, \\
& \text{(subject to online and decentralized decision-making rules)}
\end{aligned}
$$
such that the performance vector:
$$
F(x) = \big( f_1(x), f_2(x), \dots, f_k(x) \big)
$$
is Pareto optimal. This ensures that no other feasible assignment \( x' \) exists that improves one or more objectives without degrading at least one other objective.

---

This formulation precisely captures the essence of an **Online Decentralized Maximum Bipartite Matching** problem in the context of job allocation with multi-objective optimization.
