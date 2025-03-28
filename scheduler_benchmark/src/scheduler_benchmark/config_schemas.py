from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ResourceConfig:
    cpu: int
    memory_mb: int
    gpu: int = 0
    disk_gb: int = 0

@dataclass
class NodeConfig:
    """
    Represents either a head node or a compute node, holding
    a name and its ResourceConfig.
    """
    name: str
    resources: ResourceConfig
    # You can add more fields, e.g. roles, accelerators, etc.

@dataclass
class NetworkConfig:
    name: str
    cidr: str
    gateway: str

@dataclass
class StorageConfig:
    type: str
    ephemeral: bool

@dataclass
class TopologyConfig:
    """
    The overall HPC topology:
    - includes zero or more head nodes
    - includes zero or more compute nodes
    - network
    - storage
    """
    cluster_name: str
    head_nodes: List[NodeConfig] = field(default_factory=list)
    compute_nodes: List[NodeConfig] = field(default_factory=list)
    network: NetworkConfig = None
    storage: StorageConfig = None

@dataclass
class SchedulerSettings:
    """
    Optional deeper scheduler configuration. For example:
    partitions, queue settings, advanced resource usage, etc.
    """
    partition: Optional[str] = None
    version: Optional[str] = None
    # Add any domain-specific fields you need for SLURM/K8s/Flux

@dataclass
class SchedulerConfig:
    """
    Identifies which scheduler is used (SLURM, Volcano, Flux, etc.)
    plus optional advanced config (SchedulerSettings).
    """
    name: str
    settings: SchedulerSettings = None

@dataclass
class HPCConfig:
    """
    Top-level config for Hydra. Composes:
    - A Topology (A)
    - A Scheduler (B)
    - Possibly a workload definition (C) in the future
    """
    topology: TopologyConfig
    scheduler: SchedulerConfig
    # You could add a “workload” field here to represent $C
