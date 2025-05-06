from enum import Enum
from typing import List, Optional, Dict, Union
from pydantic import BaseModel, Field, field_validator


class ResourceType(str, Enum):
    CPU = "cpu"
    GPU = "gpu"
    LPU = "lpu"
    RAM = "ram"
    DISK = "disk"


class AcceleratorType(str, Enum):
    NVIDIA_A100 = "nvidia_a100"
    NVIDIA_H100 = "nvidia_h100"
    AMD_MI250 = "amd_mi250"
    INTEL_MAX = "intel_max"
    XILINX_ALVEO = "xilinx_alveo"


class Resource(BaseModel):
    type: ResourceType
    amount: int
    unit: Optional[str] = None
    accelerator_type: Optional[AcceleratorType] = None

    @field_validator("accelerator_type")
    def validate_accelerator(cls, v, values):
        if (
            values.get("type") in [ResourceType.GPU, ResourceType.LPU]
            and v is None
        ):
            raise ValueError(
                f"Accelerator type required for {values.get('type')}"
            )
        return v


class NetworkConfig(BaseModel):
    name: str
    cidr: str
    gateway: Optional[str] = None
    dns_servers: List[str] = Field(default_factory=list)


class UserConfig(BaseModel):
    name: str
    sudo: bool = False
    ssh_public_key_path: Optional[str] = None
    ssh_public_key: Optional[str] = None

    @field_validator("ssh_public_key")
    def validate_ssh_key(cls, v, values):
        if v is None and values.get("ssh_public_key_path") is None:
            return None  # Allow neither to be specified
        return v


class NodeConfig(BaseModel):
    name: str
    resources: List[Resource]
    network: NetworkConfig
    user: UserConfig
    disk_size_gb: int = 16
    image: Optional[str] = None


class ClusterConfig(BaseModel):
    name: str
    head_nodes: List[NodeConfig] = Field(default_factory=list)
    compute_nodes: List[NodeConfig] = Field(default_factory=list)


class SchedulerType(str, Enum):
    SLURM = "slurm"
    KUBERNETES = "kubernetes"
    FLUX = "flux"


class SchedulerConfig(BaseModel):
    type: SchedulerType
    version: Optional[str] = None
    partitions: Optional[List[str]] = None
    config_options: Dict[str, Union[str, int, bool, List]] = Field(
        default_factory=dict
    )


class HPCConfig(BaseModel):
    cluster: ClusterConfig
    scheduler: SchedulerConfig
