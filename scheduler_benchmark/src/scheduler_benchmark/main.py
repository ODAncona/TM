import hydra
from omegaconf import DictConfig, OmegaConf
import subprocess
import os
import colorlog
import logging

# Import your typed dataclasses
from .config_schemas import HPCConfig, TopologyConfig, SchedulerConfig, NodeConfig, ResourceConfig, NetworkConfig, StorageConfig, SchedulerSettings

@hydra.main(config_path="../../conf", config_name="config")
def main(cfg : DictConfig) -> None:
    """
    The raw `cfg` is a DictConfig from Hydra. We can convert it to HPCConfig
    if we want typed access in Python:
    """
    # Convert config to a TF-friendly dictionary or tfvars file
    # e.g., create "terraform.tfvars.json"
    # write_tfvars(cfg)
    # Then run "terraform init", "terraform apply" locally
    # subprocess.run(["terraform", "init", ...])
    # subprocess.run(["terraform", "apply", "-auto-approve", ...])
    # etc.
    
    # Another approach: do a manual conversion
    # for example:
    from omegaconf import OmegaConf

    # Convert sub-sections into HPC dataclasses:
    topology_dc = TopologyConfig(
        cluster_name=cfg.topology.cluster_name,
        head_nodes=[
            NodeConfig(
                name=node.name,
                resources=ResourceConfig(
                    cpu=node.resources.cpu,
                    memory_mb=node.resources.memory_mb,
                    disk_gb=node.resources.disk_gb
                )
            ) for node in cfg.topology.head_nodes
        ],
        compute_nodes=[
            NodeConfig(
                name=node.name,
                resources=ResourceConfig(
                    cpu=node.resources.cpu,
                    memory_mb=node.resources.memory_mb,
                    disk_gb=node.resources.disk_gb
                )
            ) for node in cfg.topology.compute_nodes
        ],
        network=NetworkConfig(
            name=cfg.topology.network.name,
            cidr=cfg.topology.network.cidr,
            gateway=cfg.topology.network.gateway
        ),
        storage=StorageConfig(
            type=cfg.topology.storage.type,
            ephemeral=cfg.topology.storage.ephemeral
        )
    )

    scheduler_dc = SchedulerConfig(
        name=cfg.scheduler.name,
        settings=SchedulerSettings(
            partition=cfg.scheduler.settings.partition
                       if "partition" in cfg.scheduler.settings
                       else None,
            version=cfg.scheduler.settings.version
                      if "version" in cfg.scheduler.settings
                      else None,
        )
    )

    # Finally, compose an HPCConfig:
    hpc_config = HPCConfig(
        topology=topology_dc,
        scheduler=scheduler_dc,
    )

    # Now you have a typed HPCConfig you can work with:
    print("======= HPC Configuration =======")
    print(hpc_config)

    # Next steps: convert these data into Terraform inputs, run provisioning, etc.
    # Example: Write out a terraform.tfvars.json or do calls directly:
    # write_tfvars(hpc_config)
    # subprocess.run(["terraform", "init"])
    # subprocess.run(["terraform", "apply", "-auto-approve"])

if __name__ == "__main__":
    import colorlog
    import logging
    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
        },
        secondary_log_colors={},
        style="%",
    )
    handler.setFormatter(formatter)
    logger = colorlog.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    main()
