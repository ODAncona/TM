import colorlog
import logging
import hydra
from omegaconf import DictConfig, OmegaConf
import os

from scheduler_benchmark.models import (
    HPCConfig, ClusterConfig, NodeConfig, Resource, 
    ResourceType, NetworkConfig, UserConfig, SchedulerConfig, SchedulerType
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
        identity_file=cfg.libvirt.identity_file
    )

    
    
    # Provision cluster
    try:
        logger.info(f"Provisioning cluster {config.cluster.name}...")
        ips = provisioner.provision_cluster(
            config.cluster,
            base_image=cfg.libvirt.base_image
        )
        
        logger.info("Cluster provisioned successfully!")
        logger.info("Node IP addresses:")
        for name, ip in ips.items():
            logger.info(f"  {name}: {ip}")
            
    except Exception as e:
        logger.error(f"Error provisioning cluster: {e}")
        
if __name__ == "__main__":
    main()
