NUMA (**Non-Uniform Memory Access**) is a computer memory architecture used in **multi-socket** and **multi-core** systems to optimize memory access speed. It divides memory into **local** regions associated with specific CPUs, reducing bottlenecks.

### **Key Concepts:**

- **Local vs. Remote Memory:** Each CPU has **faster access** to its **local memory** and **slower access** to memory assigned to another CPU.
    
- **NUMA Nodes:** Each region of memory + its associated CPUs forms a **NUMA node**.
    
- **Performance Impact:** Optimizing workloads to **use local memory** improves performance, while excessive **remote memory access** increases latency.
    

### **Example:**

A **dual-socket AMD Milan** system (like yours) has **two NUMA nodes**, each with:

- **64 cores** (per socket)
- **8 memory controllers** (per socket)
    

If a process on **Socket 1** accesses memory from **Socket 2**, performance drops due to interconnect latency.


you can pin a VM to a NUMA node with virt