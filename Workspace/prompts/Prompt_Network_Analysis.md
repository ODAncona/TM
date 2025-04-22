I need to setup a virtual cluster with vms. Each VM's img are built using nixos-generator and provisioned with a custom python libvirt script.
I need to check the internet configuration and want to evaluate whether it's better to have static IP or DHCP

here's the configuration of my network on my host
===
odancona@rhodey:~$ virsh net-dumpxml scheduler_benchmark_net
<network connections='2'>
  <name>scheduler_benchmark_net</name>
  <uuid>fa5fba2e-fd8e-4fe4-9577-6886503ff618</uuid>
  <forward mode='nat'>
    <nat>
      <port start='1024' end='65535'/>
    </nat>
  </forward>
  <bridge name='virbr2' stp='on' delay='0'/>
  <mac address='52:54:00:e0:76:1b'/>
  <domain name='scheduler_benchmark_net' localOnly='yes'/>
  <dns>
    <host ip='192.168.222.1'>
      <hostname>gateway</hostname>
    </host>
  </dns>
  <ip address='192.168.222.1' netmask='255.255.255.0' localPtr='yes'>
    <dhcp>
      <range start='192.168.222.100' end='192.168.222.254'/>
    </dhcp>
  </ip>
</network>
===

Here's my specification
===
# Benchmark Specification: Multi-Objective Comparison of HPC Schedulers

## Problem Definition

This project aims to benchmark and compare multiple HPC schedulers across different hardware and software environments. Given a benchmark function :$$F: \left(A,B,C\right) \rightarrow \left(\alpha,\beta,\gamma,\delta \right)$$composed of a virtual cluster $A$ that's running a workload $C$ on a given a Scheduler $B$ and output a set of metrics $O =\{\alpha,\beta,\gamma,\delta \}$ defined in the Output space definition section. We'll explore and analyze the pareto space related to $O$ identifying optimal trade-offs among $O$.

## Research Question

> How do SLURM, Kubernetes+Volcano, and Flux Framework schedulers compare in terms of resource utilization ($\alpha$), fairness ($\beta$), job completion time ($\gamma$), and elasticity ($\delta$) across varying HPC workloads and hardware configurations in the sense of Pareto?


## Input Space Definition

The input space $(A,B,C)$ consist of:
### Virtual Cluster $A$

- Defines the cluster architecture: number and type of head and worker nodes.
- Defines the VM nodes hardware profiles (# of CPUs,  # of GB RAM, Disk Space and network characteristics)

### Scheduler Systems $B$

The schedulers under evaluation represent distinct approaches to workload management in HPC:

1. SLURM : $b_1$
2. Kubernetes + Volcano : $b_2$
3. Flux Framework : $b_3$

### Workload Types $C$

The benchmark $F$ will be composed of :

- HPL (High Performance Linpack): Stresses CPU floating-point capabilities
- HPCG (High Performance Conjugate Gradient): Exercises memory hierarchy and interconnect
Additional workloads may be incorporated in future iterations.

## Output Space Definition

The following metrics will be used for evaluation:

- **Resource Utilization ($\alpha$)**:
  Measures the extent to which available resources (e.g., CPU, memory, network bandwidth) are employed. Higher utilization indicates more efficient use of resources, while underutilization suggests waste.

- **Fairness ($\beta$)**:
  Assesses the equitable distribution of resources among users or workloads. Finish-time fairness, for instance, compares completion time in a shared environment versus alone, ensuring no single workload monopolizes resources.

- **Job Completion Time ($\gamma$)**:
  Encompasses the entire duration required for a job to finish—queueing, execution, and teardown. Particularly important in multi-node HPC environments, where parallel processing can drastically reduce total completion time.

- **Elasticity ($\delta$)**:
  Evaluates how well the scheduler can adapt to fluctuating workloads by scaling resources up or down. Efficient elasticity ensures workload demands are met while preventing resource bottlenecks or waste.



## Hardware Resource

### Rhodey (Compute Server)

The benchmark $F$ will be executed on `rhodey`, a server in Lawrence Berkeley National Laboratory mirroring the CPU topology of a Perlmutter node.

![Perlmutter CPU nodes](https://docs.nersc.gov/systems/perlmutter/images/perlmutter_cpu_node.png)

- 2x [AMD EPYC 7763](https://www.amd.com/en/products/cpu/amd-epyc-7763) (Milan) CPUs, 64 cores per CPU
- 512 GB of DDR4 memory total
- 1x [HPE Slingshot 11](https://www.hpe.com/us/en/compute/hpc/slingshot-interconnect.html) NIC
- PCIe 4.0 NIC-CPU connection
- 4 NUMA domains per socket (NPS=4)

### X1-Carbon (Orchestration Machine)

Laptop used for orchestration, provisioning, and experiment management:

- CPU: Intel Core i7 (8th Gen)
- GPU: Intel UHD Graphics 620
- Memory: 16 GiB RAM
- OS: Arch Linux x86_64
## Methodology

The benchmarking methodology follows three distinct conceptual phases:

### Experiment Design

- Clearly define the input space (A,B,C) configurations to evaluate.
- Identify the relevant metrics (α,β,γ,δ) to measure.
- Define the experimental plan (number of repetitions, statistical significance criteria).
### Experiment Execution

- Automatically provision virtual clusters $A$ for each scheduler $B$.
- Execute workloads $C$ on each scheduler $B$ and cluster configuration $A$.
- Collect and store metrics data $O$
### Analysis and Interpretation

- For each tuple $(A,B,C)$ explore the Pareto frontier representation of $O$.
- Visualize trade-offs across metrics clearly.
- Identify bottlenecks, strengths, and weaknesses of each scheduler.
- Derive actionable guidelines for selecting schedulers based on workload types and hardware configurations.

## Architecture

The benchmark infrastructure follows those principles: 

- **Declarative Infrastructure** : All infrastructure components (VMs, networks, schedulers) are defined declaratively using Hydra and Nix flakes to ensure reproducibility.
- **Automated Provisioning** : The provisioning workflow automatically builds deterministic VM images and provisions them onto the target infrastructure using a libvirt-based Python wrapper.
- **Flexible and Extensible Architecture**: The provisioning system is designed to easily accommodate future expansions in cluster size, additional schedulers, or new workload types.
- **Observability and Reliability** : Ensure robust logging, monitoring, and error handling.
===

So
EXP configuration => hydra
os config => nixos-generator custom build image
provisionning => livirt
once the vms are provided... How can I make sure I have a kubernetes Master and kubernetes nodes that are configured to work together as a cluster ?

Here's my broken attempt
===
Project Path: scheduler_benchmark

Source Tree:

```txt
scheduler_benchmark
├── conf
│   └── config.yaml
├── nix
│   ├── modules
│   │   └── kubernetes
│   │       ├── master.nix
│   │       └── worker.nix
│   └── vm-config.nix
└── src
    └── scheduler_benchmark
        ├── __init__.py
        ├── main.py
        ├── models.py
        └── vm
            ├── __init__.py
            ├── libvirt_helper.py
            └── provision.py

```

`scheduler_benchmark/conf/config.yaml`:

```yaml
defaults:
  - override hydra/job_logging: colorlog
  - override hydra/hydra_logging: colorlog

libvirt:
  hostname: "rhodey.lbl.gov"
  username: "odancona"
  identity_file: "~/.ssh/rhodey"
  base_image: "nixos.img"
  #base_image: "ubuntu-24.04-server-cloudimg-amd64.img"
  pool_name: "scheduler_benchmark_pool"

cluster:
  name: "benchmark-cluster"
  head_nodes:
    - name: "head-node-1"
      resources:
        - type: "cpu"
          amount: 2
          unit: "cores"
        - type: "ram"
          amount: 4096
          unit: "mb"
      network:
        name: "scheduler_benchmark_net"
        cidr: "192.168.222.0/24"
        gateway: "192.168.222.1"
      user:
        name: "odancona"
        sudo: true
        ssh_public_key_path: "~/.ssh/rhodey.pub"
      disk_size_gb: 16

  compute_nodes:
    - name: "compute-node-1"
      resources:
        - type: "cpu"
          amount: 2
          unit: "cores"
        - type: "ram"
          amount: 4096
          unit: "mb"
      network:
        name: "scheduler_benchmark_net"
        cidr: "192.168.222.0/24"
        gateway: "192.168.222.1"
      user:
        name: "odancona"
        sudo: true
        ssh_public_key_path: "~/.ssh/rhodey.pub"
      disk_size_gb: 16

scheduler:
  type: "slurm"
  version: "23.02.3"
  partitions: ["compute"]
  config_options:
    SelectType: "cons_tres"

```

`scheduler_benchmark/nix/modules/kubernetes/master.nix`:

```nix
{ config, lib, pkgs, masterIP ? "192.168.222.122", ... }:

{
  services.kubernetes = {
    roles = ["master"];
    masterAddress = masterIP;
    apiserverAddress = masterIP;
    easyCerts = true;
  };

  networking.firewall.enable = true;
  networking.firewall.allowedTCPPorts = [
    22      # SSH
    6443    # Kubernetes API Server
    2379    # etcd server client API
    2380    # etcd peer communication
    10250   # Kubelet API
    10251   # kube-scheduler
    10252   # kube-controller-manager
  ];
  networking.firewall.allowedTCPPortRanges = [
    { from = 30000; to = 32767; }  # NodePort services
  ];
}
```

`scheduler_benchmark/nix/modules/kubernetes/worker.nix`:

```nix
{ config, lib, pkgs, masterIP ? "192.168.222.122", ... }:

{
  # Kubernetes Worker Node Configuration
  services.kubernetes = {
    roles = ["node"];
    masterAddress = masterIP; # dynamically provided
    apiserverAddress = masterIP; # dynamically provided
    easyCerts = true;
  };

  networking.firewall.enable = true;
  networking.firewall.allowedTCPPorts = [
    22      # SSH
    10250   # Kubelet API
  ];
  networking.firewall.allowedTCPPortRanges = [
    { from = 30000; to = 32767; }  # NodePort services
  ];
}
```

`scheduler_benchmark/nix/vm-config.nix`:

```nix
{ config, pkgs, lib, ... }:

let
  hostname = "nix-vm";
  diskSize = 16384; # 16GB in MiB
  masterIP = "192.168.222.122";

  baseSystem = { ... }: {
    boot.kernelPackages = pkgs.linuxPackages_6_1;
    boot.loader.systemd-boot.enable = true;
    boot.loader.efi.canTouchEfiVariables = true;

    networking.hostName = hostname;
    networking.useDHCP = true;
    networking.useNetworkd = true;
    systemd.network.enable = true;

    nix.settings.experimental-features = [ "nix-command" "flakes" ];
    time.timeZone = "UTC";

    users.users.odancona = {
      isNormalUser = true;
      initialPassword = "password";
      extraGroups = [ "wheel" ];
      openssh.authorizedKeys.keys = [
        (builtins.readFile /home/olivier/.ssh/rhodey.pub)
        (builtins.readFile /home/olivier/.ssh/id_ed25519.pub)
      ];
    };

    services.openssh.enable = true;

    environment.systemPackages = with pkgs; [
      vim
      curl
      tree
      btop
      bat
      fastfetch
    ];

    swapDevices = [];
    virtualisation.diskSize = lib.mkForce diskSize;
  };

    masterConfig = import ./modules/kubernetes/master.nix { 
    inherit config lib pkgs;
    masterIP = masterIP;
  };

in
{
  imports = [
    (baseSystem { })
    # Uncomment below according to node role
    masterConfig
  ];

  system.stateVersion = "24.11";
}
```

`scheduler_benchmark/src/scheduler_benchmark/__init__.py`:

```py
def hello() -> str:
    return "Hello from scheduler-benchmark!"

```

`scheduler_benchmark/src/scheduler_benchmark/main.py`:

```py
import colorlog
import logging
import hydra
from omegaconf import DictConfig, OmegaConf
import os

from scheduler_benchmark.models import (
    HPCConfig,
    ClusterConfig,
    NodeConfig,
    Resource,
    ResourceType,
    NetworkConfig,
    UserConfig,
    SchedulerConfig,
    SchedulerType,
)
from scheduler_benchmark.vm.provision import VMProvisioner

logger = logging.getLogger(__name__)


def config_to_model(cfg: DictConfig) -> HPCConfig:
    """Convert Hydra config to Pydantic model"""
    # This handles conversion from DictConfig to our Pydantic models
    # Convert to dict first to remove OmegaConf specifics
    cfg_dict = OmegaConf.to_container(cfg, resolve=True)
    return HPCConfig.model_validate(cfg_dict)


@hydra.main(version_base=None, config_path="../../conf", config_name="config")
def main(cfg: DictConfig) -> None:
    """Main entry point with Hydra configuration"""
    # Convert hydra config to pydantic model
    try:
        config = config_to_model(cfg)
        logger.info(f"Loaded configuration for cluster: {config.cluster.name}")
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return

    # Create VM provisioner for the remote host
    provisioner = VMProvisioner(
        hostname=cfg.libvirt.hostname,
        username=cfg.libvirt.username,
        identity_file=cfg.libvirt.identity_file,
        pool_name=cfg.libvirt.pool_name,
    )

    try:
        # Provision a single node
        node = config.cluster.head_nodes[
            0
        ]  # Example: provision the first head node
        print(type(node))
        ip = provisioner.provision_node(node, base_image=cfg.libvirt.base_image)
        logger.info(f"Node {node.name} provisioned with IP: {ip}")
    except Exception as e:
        logger.error(f"Error provisioning node: {e}")
        return

    # Provision cluster
    # try:
    #     logger.info(f"Provisioning cluster {config.cluster.name}...")
    #     ips = provisioner.provision_cluster(
    #         config.cluster,
    #         base_image=cfg.libvirt.base_image
    #     )

    #     logger.info("Cluster provisioned successfully!")
    #     logger.info("Node IP addresses:")
    #     for name, ip in ips.items():
    #         logger.info(f"  {name}: {ip}")

    # except Exception as e:
    #     logger.error(f"Error provisioning cluster: {e}")


if __name__ == "__main__":
    main()

```

`scheduler_benchmark/src/scheduler_benchmark/models.py`:

```py
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
            values.get("type") in [ResourceType.GPU, ResourceType.FPGA]
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

```

`scheduler_benchmark/src/scheduler_benchmark/vm/libvirt_helper.py`:

```py
"""
This modules is a wrapper around livirt to manages VMs and storage
"""

import libvirt
import os
import time
import tempfile
from scheduler_benchmark.models import NodeConfig, Resource, ResourceType
import logging


class LibvirtConnection:
    def __init__(
        self,
        hostname: str,
        username: str | None = None,
        identity_file: str | None = None,
        pool_name: str = "default",
        logger: logging.Logger | None = None,
    ):
        self.hostname = hostname
        self.username = username
        self.identity_file = identity_file
        self.ssh_config_file = None
        self.conn = None
        self.pool_name = pool_name
        self.logger = logger or logging.getLogger(__name__)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def _create_ssh_config(self):
        """Create a temporary SSH config file to force key-based authentication"""
        if not self.identity_file:
            return None

        expanded_identity = os.path.expanduser(self.identity_file)
        self.logger.debug(
            f"Création d'un fichier de configuration SSH avec la clé {expanded_identity}"
        )

        # Create temporary SSH config file
        ssh_config_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
        ssh_config_file.write(
            f"""Host {self.hostname}
    IdentityFile {expanded_identity}
    PasswordAuthentication no
    PubkeyAuthentication yes
    BatchMode yes
    StrictHostKeyChecking no
    """
        )
        ssh_config_file.close()
        self.logger.debug(
            f"Fichier de configuration SSH créé: {ssh_config_file.name}"
        )
        return ssh_config_file.name

    def connect(self):
        if not self.conn:
            self.logger.info(f"Connexion à l'hôte libvirt {self.hostname}")
            try:
                # Create SSH config
                if self.identity_file:
                    self.ssh_config_file = self._create_ssh_config()
                    expanded_identity = os.path.expanduser(self.identity_file)

                    # Configure libvirt SSH environment
                    uri = f"qemu+ssh://{self.username}@{self.hostname}/system?no_verify=1&keyfile={expanded_identity}&no_tty=1"
                    os.environ["LIBVIRT_DEFAULT_URI"] = uri
                    os.environ["LIBVIRT_SSH_KEY"] = expanded_identity
                    os.environ["LIBVIRT_SSH_CONFIG"] = self.ssh_config_file

                    self.logger.debug(f"Utilisation de l'URI: {uri}")

                    # Connect using the specified URI
                    self.conn = libvirt.open(uri)
                else:
                    # Standard connection without SSH key
                    uri = f"qemu+ssh://{self.username}@{self.hostname}/system"
                    self.logger.debug(f"Utilisation de l'URI standard: {uri}")
                    self.conn = libvirt.open(uri)

                self.logger.info(f"Connexion réussie à {self.hostname}")
            except libvirt.libvirtError as e:
                self.logger.error(
                    f"Échec de connexion à {self.hostname}: {str(e)}"
                )
                raise

        return self.conn

    def disconnect(self):
        if self.conn:
            self.logger.info(f"Déconnexion de l'hôte libvirt {self.hostname}")
            self.conn.close()
            self.conn = None

        # Clean up temporary SSH config file
        if self.ssh_config_file and os.path.exists(self.ssh_config_file):
            self.logger.debug(
                f"Suppression du fichier de configuration SSH temporaire: {self.ssh_config_file}"
            )
            os.unlink(self.ssh_config_file)
            self.ssh_config_file = None

    def get_vm(self, name: str) -> libvirt.virDomain | None:
        """Get a VM by name"""
        try:
            vm = self.conn.lookupByName(name)
            self.logger.debug(f"VM '{name}' trouvée")
            return vm
        except libvirt.libvirtError:
            self.logger.debug(f"VM '{name}' non trouvée")
            return None

    def vm_exists(self, name: str) -> bool:
        """Check if a VM exists"""
        return self.get_vm(name) is not None

    def create_volume(
        self, name: str, size_gb: int, base_image: str | None = None
    ) -> str:
        """Create a new volume, optionally based on an image"""
        if self.conn is None:
            self.logger.error(
                "Tentative de création de volume sans connexion établie"
            )
            raise RuntimeError("Not connected to libvirt")

        size_bytes = size_gb * 1024 * 1024 * 1024
        self.logger.info(
            f"Création du volume '{name}' de {size_gb}GB"
            + (f" basé sur '{base_image}'" if base_image else "")
        )

        # Get storage pool
        try:
            pool = self.conn.storagePoolLookupByName(self.pool_name)
        except libvirt.libvirtError as e:
            self.logger.error(
                f"Impossible de trouver le pool de stockage '{self.pool_name}': {str(e)}"
            )
            raise

        if base_image:
            try:
                # Try to use as volume name in pool (standard approach)
                base_vol = pool.storageVolLookupByName(base_image)
                self.logger.debug(
                    f"Image de base '{base_image}' trouvée dans le pool"
                )

                # Create volume from base image
                vol_xml = f"""
                <volume>
                    <name>{name}</name>
                    <capacity unit="bytes">{size_bytes}</capacity>
                    <target>
                        <format type="qcow2"/>
                    </target>
                </volume>
                """
                volume = pool.createXMLFrom(vol_xml, base_vol, 0)

            except libvirt.libvirtError as e:
                self.logger.warning(
                    f"Base image '{base_image}' non trouvée dans le pool: {str(e)}"
                )
                # If it's not in the pool, check if it's a full path on the remote system
                if os.path.isabs(base_image):
                    # For absolute paths, we can try to use the vol-create-from command
                    # which is what administrators typically use
                    error_msg = (
                        f"Base image '{base_image}' not found in pool '{self.pool_name}', but looks like a path. "
                        f"Try importing it first with: virsh vol-create-as {self.pool_name} {os.path.basename(base_image)} --format qcow2"
                    )
                    self.logger.error(error_msg)
                    print(error_msg)

                # Fail with a helpful error message
                error_msg = (
                    f"Base image '{base_image}' not found in storage pool '{self.pool_name}'. "
                    f"Please add it to the pool first using standard libvirt tools."
                )
                self.logger.error(error_msg)
                raise ValueError(error_msg)
        else:
            # Create empty volume
            vol_xml = f"""
            <volume>
                <name>{name}</name>
                <capacity unit="bytes">{size_bytes}</capacity>
                <target>
                    <format type="qcow2"/>
                </target>
            </volume>
            """
            volume = pool.createXML(vol_xml, 0)

        volume_path = volume.path()
        self.logger.info(f"Volume '{name}' créé avec succès: {volume_path}")
        return volume_path

    def delete_volume(self, name: str) -> bool:
        """Delete a volume"""
        self.logger.info(f"Suppression du volume '{name}'")
        try:
            pool = self.conn.storagePoolLookupByName(self.pool_name)
            volume = pool.storageVolLookupByName(name)
            volume.delete(0)
            self.logger.info(f"Volume '{name}' supprimé avec succès")
            return True
        except libvirt.libvirtError as e:
            self.logger.warning(
                f"Échec de la suppression du volume '{name}': {str(e)}"
            )
            return False

    def create_vm(
        self,
        node_config: NodeConfig,
        base_image: str | None = None,
        wait_time: int = 30,
    ) -> tuple[libvirt.virDomain, str]:
        """Create a VM based on node configuration"""
        if self.conn is None:
            raise RuntimeError("Not connected to libvirt")
        # Create volume
        volume_path = self.create_volume(
            f"{node_config.name}_disk",
            node_config.disk_size_gb,
            base_image,
        )

        # Extract resources
        for res in node_config.resources:
            if res.type == ResourceType.RAM:
                memory_mb = res.amount
            elif res.type == ResourceType.CPU:
                vcpus = res.amount

        # Create VM XML
        vm_xml = f"""
        <domain type='kvm'>
            <name>{node_config.name}</name>
            <memory unit='MiB'>{memory_mb}</memory>
            <vcpu>{vcpus}</vcpu>
            <os>
                <type arch='x86_64'>hvm</type>
                <boot dev='hd'/>
            </os>
            <devices>
                <disk type='file' device='disk'>
                    <driver name='qemu' type='qcow2'/>
                    <source file='{volume_path}'/>
                    <target dev='vda' bus='virtio'/>
                </disk>
                <interface type='network'>
                    <source network='{node_config.network.name}'/>
                    <model type='virtio'/>
                </interface>
                <console type='pty'>
                    <target type='serial' port='0'/>
                </console>
                <graphics type='spice' autoport='yes' listen='127.0.0.1'>
                    <listen type='address' address='127.0.0.1'/>
                </graphics>
            </devices>
        </domain>
        """

        domain = self.conn.defineXML(vm_xml)
        domain.create()
        self.logger.info(
            f"VM {node_config.name} créée, en attente d'une adresse IP..."
        )

        # Get IP address (may take some time)
        ip_address = None
        for _ in range(wait_time):
            try:
                ifaces = domain.interfaceAddresses(
                    libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE
                )
                for _, data in ifaces.items():
                    for addr in data.get("addrs", []):
                        if addr["type"] == libvirt.VIR_IP_ADDR_TYPE_IPV4:
                            ip_address = addr["addr"]
                            break
                if ip_address:
                    break
            except libvirt.libvirtError:
                pass
            time.sleep(1)

        return domain, ip_address

    def delete_vm(self, name: str, delete_storage: bool = True) -> bool:
        """Delete a VM and optionally its storage"""
        self.logger.info(
            f"Suppression de la VM '{name}'"
            + (" avec stockage" if delete_storage else "")
        )

        domain = self.get_vm(name)
        if not domain:
            self.logger.warning(f"VM '{name}' non trouvée")
            return False

        # Get disks before shutting down
        disks = []
        if delete_storage:
            xml = domain.XMLDesc()
            # Simple parsing - in production code use proper XML parsing
            for line in xml.split("\n"):
                if "<source file='" in line and "cdrom" not in line:
                    disk_path = line.split("'")[1]
                    disks.append(disk_path)
                    self.logger.debug(f"Disque trouvé à supprimer: {disk_path}")

        # Shutdown VM if running
        if domain.isActive():
            self.logger.debug(f"Arrêt forcé de la VM '{name}'")
            domain.destroy()

        # Undefine VM
        try:
            domain.undefineFlags(libvirt.VIR_DOMAIN_UNDEFINE_NVRAM)
            self.logger.debug(f"VM '{name}' supprimée de la configuration")
        except libvirt.libvirtError as e:
            self.logger.error(
                f"Erreur lors de la suppression de la VM '{name}': {str(e)}"
            )
            return False

        # Delete storage
        if delete_storage:
            for disk_path in disks:
                try:
                    vol = self.conn.storageVolLookupByPath(disk_path)
                    vol.delete(0)
                    self.logger.debug(f"Disque supprimé: {disk_path}")
                except libvirt.libvirtError as e:
                    self.logger.warning(
                        f"Impossible de supprimer le disque {disk_path}: {str(e)}"
                    )

        self.logger.info(f"VM '{name}' supprimée avec succès")
        return True

```

`scheduler_benchmark/src/scheduler_benchmark/vm/provision.py`:

```py
from scheduler_benchmark.models import NodeConfig, HPCConfig, ClusterConfig
from scheduler_benchmark.vm.libvirt_helper import LibvirtConnection


class VMProvisioner:
    def __init__(
        self,
        hostname: str,
        username: str | None = None,
        identity_file: str | None = None,
        pool_name: str = "default",
    ):
        self.hostname = hostname
        self.username = username
        self.identity_file = identity_file
        self.pool_name = pool_name

    def provision_node(
        self, node: NodeConfig, base_image: str | None = None
    ) -> str:
        """Provision a single node and return its IP address"""
        # Create VM using libvirt
        with LibvirtConnection(
            self.hostname, self.username, self.identity_file, self.pool_name
        ) as conn:
            domain, ip_address = conn.create_vm(node, base_image)
            return ip_address

    def provision_cluster(
        self, cluster: ClusterConfig, base_image: str | None = None
    ) -> dict[str, str]:
        """Provision an entire cluster from a cluster config"""
        ips = {}

        # Provision head nodes
        for node in cluster.head_nodes:
            ip = self.provision_node(node, base_image)
            ips[node.name] = ip

        # Provision compute nodes
        for node in cluster.compute_nodes:
            ip = self.provision_node(node, base_image)
            ips[node.name] = ip

        return ips

    def delete_node(self, node_name: str) -> bool:
        """Delete a node by name"""
        with LibvirtConnection(
            self.hostname, self.username, self.identity_file
        ) as conn:
            return conn.delete_vm(node_name)

    def delete_cluster(self, cluster: ClusterConfig) -> dict[str, bool]:
        """Delete all nodes in a cluster"""
        results = {}

        # Delete all nodes
        with LibvirtConnection(
            self.hostname, self.username, self.identity_file
        ) as conn:
            # Delete head nodes
            for node in cluster.head_nodes:
                results[node.name] = conn.delete_vm(node.name)

            # Delete compute nodes
            for node in cluster.compute_nodes:
                results[node.name] = conn.delete_vm(node.name)

        return results

```
===

Provide an analysis of the configuration after the VMs are spawned