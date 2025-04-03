import subprocess
import tempfile
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from scheduler_benchmark.models import NodeConfig

class NixHelper:
    def __init__(self, hostname: str, username: str, identity_file: str):
        self.hostname = hostname
        self.username = username
        self.identity_file = identity_file

    def generate_nixos_config(self, node: NodeConfig) -> Path:
        """Generates a configuration.nix file using Jinja2 templating."""
        env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
        template = env.get_template('configuration.nix.j2')

        # Prepare context for Jinja2 template
        context = {
            'node_name': node.name,
            'resources': node.resources,
            'network': node.network,
            'user': node.user,
            'ssh_key': node.user.ssh_public_key,
            # Add other relevant data from NodeConfig as needed
        }

        rendered_config = template.render(context)
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".nix") as temp_file:
            temp_file.write(rendered_config)
            return Path(temp_file.name)

    def configure_nixos(self, node: NodeConfig, config_nix_path: Path):
        """Installs and configures NixOS on the VM."""
        try:
            # Copy configuration.nix to the VM
            subprocess.run(
                ["scp", str(config_nix_path), f"root@{self.hostname}:/etc/nixos/configuration.nix"],
                check=True,
                capture_output=True,
                text=True
            )

            # Install and configure NixOS
            subprocess.run(
                ["ssh", f"{self.username}@{self.hostname}", f"sudo nixos-install --no-reboot"],
                check=True,
                capture_output=True,
                text=True
            )
            subprocess.run(
                ["ssh", f"{self.username}@{self.hostname}", "sudo nixos-rebuild switch"],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"NixOS configuration successful for {node.name}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error configuring NixOS on {node.name}: {e.stderr}")
        finally:
            # Clean up temporary file
            Path(config_nix_path).unlink()