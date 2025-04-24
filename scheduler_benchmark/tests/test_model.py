# tests/test_config_parsing.py
import pytest
from omegaconf import OmegaConf
from scheduler_benchmark.models import (
    ResourceType,
    AcceleratorType,
    Resource,
    NetworkConfig,
    UserConfig,
    NodeConfig,
    ClusterConfig,
    SchedulerType,
    SchedulerConfig,
    HPCConfig,
)


@pytest.fixture
def head_node_config():
    return NodeConfig(
        name="head-node-1",
        resources=[
            Resource(type=ResourceType.CPU, amount=2, unit="cores"),
            Resource(type=ResourceType.RAM, amount=4096, unit="mb"),
        ],
        network=NetworkConfig(
            name="scheduler_benchmark_net",
            cidr="192.168.222.0/24",
            gateway="192.168.222.1",
        ),
        user=UserConfig(
            name="odancona", sudo=True, ssh_public_key_path="~/.ssh/rhodey.pub"
        ),
        disk_size_gb=16,
        image="nixos-k8s-master.img"
    )


@pytest.fixture
def compute_node_config():
    return NodeConfig(
        name="compute-node-1",
        resources=[
            Resource(type=ResourceType.CPU, amount=2, unit="cores"),
            Resource(type=ResourceType.RAM, amount=4096, unit="mb"),
        ],
        network=NetworkConfig(
            name="scheduler_benchmark_net",
            cidr="192.168.222.0/24",
            gateway="192.168.222.1",
        ),
        user=UserConfig(
            name="odancona", sudo=True, ssh_public_key_path="~/.ssh/rhodey.pub"
        ),
        disk_size_gb=16,
        image="nixos-k8s-worker.img",
    )


@pytest.fixture
def scheduler_config():
    return SchedulerConfig(
        type=SchedulerType.SLURM,
        version="23.02.3",
        partitions=["compute"],
        config_options={"SelectType": "cons_tres"},
    )


@pytest.fixture
def cluster_config(head_node_config, compute_node_config):
    return ClusterConfig(
        name="benchmark-cluster",
        head_nodes=[head_node_config],
        compute_nodes=[compute_node_config],
    )


@pytest.fixture
def hpc_config(cluster_config, scheduler_config):
    return HPCConfig(cluster=cluster_config, scheduler=scheduler_config)


def test_config_parsing(hpc_config):
    """Tests parsing the config.yaml file and converting it to the HPCConfig model using fixtures."""
    config = OmegaConf.load("conf/config.yaml")
    config_dict = OmegaConf.to_container(config, resolve=True)

    try:
        loaded_hpc_config = HPCConfig.model_validate(config_dict)
    except Exception as e:
        pytest.fail(f"Failed to validate config: {e}")

    # Compare the loaded config with the fixture config
    assert loaded_hpc_config == hpc_config


def test_parse_node_config():
    config = OmegaConf.load("conf/config.yaml")
    head_node_data = config.cluster.head_nodes[0]
    head_node = NodeConfig(**head_node_data)
    assert isinstance(head_node, NodeConfig)
    assert head_node.name == "head-node-1"


def test_parse_user_config():
    config = OmegaConf.load("conf/config.yaml")
    head_node_data = config.cluster.head_nodes[0]
    user_config = UserConfig(**head_node_data.user)
    assert isinstance(user_config, UserConfig)
    assert user_config.name == "odancona"


def test_parse_network_config():
    config = OmegaConf.load("conf/config.yaml")
    head_node_data = config.cluster.head_nodes[0]
    network_config = NetworkConfig(**head_node_data.network)
    assert isinstance(network_config, NetworkConfig)
    assert network_config.name == "scheduler_benchmark_net"
