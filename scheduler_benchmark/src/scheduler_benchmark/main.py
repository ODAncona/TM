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

    provisioner.delete_cluster(config.cluster)

    try:
        # Provision the master node
        node = config.cluster.head_nodes[0]
        ip = provisioner.provision_node(node)
        logger.info(f"Node {node.name} provisioned with IP: {ip}")

        # Provision the worker nodes
        for node in config.cluster.compute_nodes:
            ip = provisioner.provision_node(node)
            logger.info(f"Node {node.name} provisioned with IP: {ip}")
    except Exception as e:
        logger.error(f"Error provisioning node: {e}")
        return

    # Provision cluster
    # try:
    #     logger.info(f"Provisioning k8s cluster {config.cluster.name}...")
    #     master_ip = provisioner.provision_k8s_cluster(
    #         config.cluster,
    #     )
    #     logger.info(f"Master node IP: {master_ip}")
    #     logger.info("Cluster provisioned successfully!")
    #     logger.info("Node IP addresses:")

    # except Exception as e:
    #     logger.error(f"Error provisioning cluster: {e}")


if __name__ == "__main__":
    main()
