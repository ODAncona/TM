import pytest
from scheduler_benchmark.vm.provision import VMProvisioner
from scheduler_benchmark.models import NodeConfig, Resource, ResourceType, NetworkConfig, UserConfig
import os
from omegaconf import OmegaConf

# Load configuration from config.yaml
cfg = OmegaConf.load("conf/config.yaml")

@pytest.fixture(scope="module")
def provisioner():
    return VMProvisioner(
        hostname=cfg.libvirt.hostname,
        username=cfg.libvirt.username,
        identity_file=cfg.libvirt.identity_file,
        pool_name=cfg.libvirt.pool_name
    )

@pytest.fixture
def test_node_config(request):
    # Use unique names to avoid conflicts
    unique_name = f"pytest_remote_{request.node.nodeid.replace('/', '_')}"
    # Extract relevant data using OmegaConf.select to handle potential config changes gracefully
    network_config_data = OmegaConf.select(cfg, "cluster.head_nodes[0].network")
    user_config_data = OmegaConf.select(cfg, "cluster.head_nodes[0].user")

    return NodeConfig(
        name=unique_name,
        resources=[Resource(type=ResourceType.CPU, amount=1), Resource(type=ResourceType.RAM, amount=2048)],
        network=NetworkConfig(**network_config_data),  # Use ** to unpack the dictionary
        user=UserConfig(**user_config_data),         # Use ** to unpack the dictionary
        image=cfg.libvirt.base_image,
        disk_size_gb=10
    )

def test_provision_and_delete_node(provisioner, test_node_config):
    try:
        ip = provisioner.provision_node(test_node_config, base_image=cfg.libvirt.base_image)
        assert ip is not None  # Check if an IP was assigned (this might still fail)
        print(f"Provisioned node {test_node_config.name} with IP: {ip}")  # For debugging
    finally:
        # Always clean up, even if the test fails
        provisioner.delete_node(test_node_config.name)