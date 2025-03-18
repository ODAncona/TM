## CPU Performance Metrics (PAPI)

The Performance Application Programming Interface (PAPI) provides standardized access to hardware performance counters across different CPU architectures. These metrics offer deep insights into how effectively the computational cores are being utilized:

### Instruction and Cycle Metrics
- **PAPI_TOT_INS**: Total number of instructions completed by the CPU. This fundamental metric helps measure computational throughput and can be used to calculate instructions per cycle (IPC) when paired with cycle counts.
- **PAPI_REF_CYC**: Reference clock cycles elapsed. This represents the hardware timing reference and is critical for normalizing other performance metrics across different CPU frequencies.
- **PAPI_FP_INS**: Floating-point instructions executed. This counter is particularly important for HPC workloads, as it directly measures computational intensity for scientific applications.

### Memory Hierarchy Metrics
- **PAPI_L3_TCM**: L3 cache total misses. The Last Level Cache (LLC) misses indicate when data must be retrieved from main memory, which is significantly slower than cache access.
- **PAPI_L3_LDM**: L3 cache load misses. Specifically tracks when read operations miss the L3 cache.
- **PAPI_L3_STM**: L3 cache store misses. Measures when write operations miss the L3 cache.
- **PAPI_PRF_DM**: Data prefetch cache misses. Tracks when the hardware prefetcher fails to accurately predict memory access patterns.

### Memory Stall Metrics
- **PAPI_MEM_SCY**: Cycles stalled waiting for memory access. This metric shows CPU idle time due to memory subsystem latency.
- **PAPI_MEM_RCY**: Cycles stalled waiting specifically for memory reads. This helps pinpoint read-dependent memory bottlenecks.

## GPU CPU Utilization

- **cpu_00_load through cpu_03_load**: Per-core CPU utilization metrics on the GPU node. These show how compute load is distributed across the CPU cores that support each GPU, revealing potential CPU bottlenecks in GPU-accelerated applications.
- **cpu_load**: Aggregate CPU utilization across all cores attached to the GPU. This provides a higher-level view of host CPU utilization.

## GPU Core Performance Metrics

- **GPU_busy**: Percentage of time the GPU is actively executing kernels. This is the primary indicator of GPU computational utilization.
- **GPU_idle**: Percentage of time the GPU spends with no work to do. High idle time suggests underutilization or bottlenecks elsewhere.
- **GPU Bottleneck**: Diagnostic indicator that helps identify what's limiting GPU performance (memory throughput, PCIe bandwidth, etc.).

### GPU Cache Metrics
- **l1_global_load_transactions_miss**: L1 cache misses during global memory load operations. High miss rates indicate suboptimal memory access patterns.
- **l1_global_store_transactions**: Global memory store operations that may bypass the L1 cache depending on architecture.
- **l1_local_load_transactions_miss**: L1 cache misses during local memory load operations.
- **l1_local_store_transactions_miss**: L1 cache misses during local memory store operations.

## GPU Memory and Interconnect Bandwidth

- **PROF_DRAM_ACTIVE**: GPU HBM2 memory bandwidth utilization. This measures how effectively applications are using the high-bandwidth memory on the GPUs.
- **PROF_NVLINK_[T|R]X_BYTES**: NVLink transmitted and received bytes. NVLink provides high-speed GPU-to-GPU communication, critical for multi-GPU workloads.
- **PROF_PCIE_[T|R]X_BYTES**: PCIe transmitted and received bytes. This measures host-to-GPU communication bandwidth, which can be a bottleneck for data-intensive applications.

## Network Interface Controller (NIC) Metrics

### Traffic Classification
- **HNI_PKTS_SENT_BY_TC_\<n\> and HNI_PKTS_RECV_BY_TC_\<n\>**: Packets sent/received by traffic class (0-7). These metrics show network traffic separated by priority levels, which is important for understanding quality of service impacts.
- **HNI_RX_PAUSED_\<n\>**: Receive flow control paused events by traffic class. These indicate when network congestion forces traffic throttling.

### Packet Size Distribution
- **HNI_TX_OK_\<min\>_to_\<max\> and HNI_RX_OK_\<min\>_to_\<max\>**: Successful transmit/receive operations binned by size across 12 bins. This histogram reveals the packet size distribution, which affects network efficiency.

### Latency Metrics
- **PCT_HOST_ACCESS_LATENCY**: Histograms showing host memory access latency distribution. These indicate how long it takes for the NIC to access host memory.
- **PCT_REQ_RSP_LATENCY**: Histograms showing request-response latency distribution. These measure end-to-end communication timing.

These comprehensive metrics collectively provide deep visibility into computational efficiency, memory system performance, GPU utilization, and network behavior—all critical dimensions for understanding HPC application performance characteristics and potential optimization opportunities.