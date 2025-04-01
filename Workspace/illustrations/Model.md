
@startuml

enum ResourceType {
    CPU
    GPU
    FPGA
    RAM
    DISK
}

enum AcceleratorType {
    NVIDIA_A100
    NVIDIA_H100
    AMD_MI250
    INTEL_MAX
    XILINX_ALVEO
}

enum SchedulerType {
    SLURM
    KUBERNETES
    FLUX
}

class Resource {
    type: ResourceType
    amount: int
    unit: Optional[str]
    accelerator_type: Optional[AcceleratorType]
}

class NetworkConfig {
    name: str
    cidr: str
    gateway: Optional[str]
    dns_servers: List[str]
}

class UserConfig {
    name: str
    sudo: bool
    ssh_public_key_path: Optional[str]
    ssh_public_key: Optional[str]
}

class NodeConfig {
    name: str
    resources: List[Resource]
    network: NetworkConfig
    user: UserConfig
    image: str
    disk_size_gb: int
}

class ClusterConfig {
    name: str
    head_nodes: List[NodeConfig]
    compute_nodes: List[NodeConfig]
}

class SchedulerConfig {
    type: SchedulerType
    version: Optional[str]
    partitions: Optional[List[str]]
    config_options: Dict[str, Union[str, int, bool, List]]
}

class HPCConfig {
    cluster: ClusterConfig
    scheduler: SchedulerConfig
}

Resource --|> ResourceType
Resource --> AcceleratorType : accelerator_type
NodeConfig --> Resource : resources
NodeConfig --> NetworkConfig : network
NodeConfig --> UserConfig : user
ClusterConfig --> NodeConfig : head_nodes
ClusterConfig --> NodeConfig : compute_nodes
SchedulerConfig --|> SchedulerType
HPCConfig --> ClusterConfig : cluster
HPCConfig --> SchedulerConfig : scheduler

@enduml
