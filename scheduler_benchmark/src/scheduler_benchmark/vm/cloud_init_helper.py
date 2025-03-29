import os
import tempfile
import subprocess
import yaml
from scheduler_benchmark.models import NodeConfig, UserConfig

class CloudInitHelper:
    def __init__(self, work_dir: str | None = None):
        self.work_dir = work_dir or tempfile.mkdtemp()
        
    def generate_user_data(self, node: NodeConfig) -> str:
        """Generate cloud-init user-data from node config"""
        user = node.user
        
        # Get SSH key
        ssh_key = None
        if user.ssh_public_key:
            ssh_key = user.ssh_public_key
        elif user.ssh_public_key_path:
            with open(os.path.expanduser(user.ssh_public_key_path), 'r') as f:
                ssh_key = f.read().strip()
                
        # Build cloud-init config
        cloud_config = {
            "hostname": node.name,
            "ssh_pwauth": True,
            "users": [
                {
                    "name": user.name,
                    "sudo": ["ALL=(ALL) NOPASSWD:ALL"] if user.sudo else [],
                    "groups": "sudo" if user.sudo else "",
                    "shell": "/bin/bash"
                }
            ],
            "growpart": {
                "mode": "auto",
                "devices": ["/"]
            },
            "runcmd": [
                "resize2fs /dev/vda1"
            ]
        }
        
        # Add SSH key if present
        if ssh_key:
            cloud_config["users"][0]["ssh_authorized_keys"] = [ssh_key]
            
        return "#cloud-config\n" + yaml.dump(cloud_config)
        
    def generate_meta_data(self, node: NodeConfig) -> str:
        """Generate cloud-init meta-data"""
        # Simple metadata with instance-id
        meta_data = {
            "instance-id": node.name,
            "local-hostname": node.name
        }
        return yaml.dump(meta_data)
        
    def create_cloud_init_iso(self, node: NodeConfig) -> str:
        """Create a cloud-init ISO file for the given node"""
        user_data = self.generate_user_data(node)
        meta_data = self.generate_meta_data(node)
        
        # Create files
        user_data_path = os.path.join(self.work_dir, "user-data")
        meta_data_path = os.path.join(self.work_dir, "meta-data")
        iso_path = os.path.join(self.work_dir, f"{node.name}-cloud-init.iso")
        
        with open(user_data_path, 'w') as f:
            f.write(user_data)
            
        with open(meta_data_path, 'w') as f:
            f.write(meta_data)
            
        # Create ISO
        try:
            subprocess.run([
                "genisoimage", "-output", iso_path, 
                "-volid", "cidata", "-joliet", "-rock",
                user_data_path, meta_data_path
            ], check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create cloud-init ISO: {e}")
            
        return iso_path