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