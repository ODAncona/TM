from scheduler_benchmark.models import NodeConfig, HPCConfig, ClusterConfig
from scheduler_benchmark.vm.libvirt_helper import LibvirtConnection
import paramiko
import time
import logging
from pathlib import Path


class VMProvisioner:
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
        self.pool_name = pool_name
        self.logger = logger or logging.getLogger(__name__)

    def provision_node(
        self, node_config: NodeConfig
    ) -> str:
        """Provision a single node and return its IP address"""
        # Create VM using libvirt
        with LibvirtConnection(
            self.hostname, self.username, self.identity_file, self.pool_name
        ) as conn:
            domain, ip_address = conn.create_vm(node_config)
            if not ip_address:
                raise RuntimeError(
                    f"VM {node_config.name} did not obtain an IP"
                )
            return ip_address

    def provision_k8s_cluster(self, cluster: ClusterConfig):
        master_ip = self.provision_node(cluster.head_nodes[0])

        try:
            self.wait_ssh_ready(master_ip)
        except Exception:
            self.logger.error(f"Master SSH not ready: {master_ip}")
            raise RuntimeError("Master SSH not ready")

        join_k8s_token = self.ssh_execute(master_ip, "sudo cat /var/lib/kubernetes/secrets/apitoken.secret")
        self.logger.info(f"Token: {join_k8s_token}")

        for node_config in cluster.compute_nodes:
            ip = self.provision_node(node_config)
            try:
                self.ssh_execute(ip, "true")
            except Exception:
                self.logger.error(f"Worker SSH not ready: {ip}")
                raise RuntimeError("Worker SSH not ready")
            self.ssh_execute(ip, f"sudo hostnamectl set-hostname {node_config.name}")
            self.logger.debug(f"Joining {ip} ...")
            cmd = f"echo {join_k8s_token} | sudo nixos-kubernetes-node-join"
            self.logger.info(self.ssh_execute(ip, cmd))

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

    def wait_ssh_ready(self, host, timeout=90, interval=3):
        start = time.time()
        while time.time() - start < timeout:
            try:
                self.ssh_execute(host, "true")
                return
            except Exception as e:
                self.logger.error(f"SSH not ready on {host}: {e}")
                time.sleep(interval)
        raise TimeoutError(f"SSH not ready on {host} after {timeout}s")

    def ssh_execute(self, host, command):
        """
        SSH into the host and execute a command via jump host (rhodey).

        self.hostname must be the jump host (rhodey).
        self.identity_file must be the private key for the jump host and the VM. /!\
        host must be the VM hostname or IP address.
        """
        key_path = str(Path(self.identity_file).expanduser())


        # ~~~ Jump host ~~~
        jump_client = paramiko.SSHClient()
        jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.logger.debug(f"Connecting to jump host {self.hostname} as {self.username} with {self.identity_file}")
        jump_client.connect(
            self.hostname,
            username=self.username,
            key_filename=key_path,
            allow_agent=True,
            look_for_keys=True,
        )

        # ~~~ Tunnel to the VM ~~~
        jump_transport = jump_client.get_transport()
        dest_addr = (host, 22)
        local_addr = ('', 0)  # source address, can be blank
        self.logger.debug(f"Creating tunnel to {host} via {self.hostname}")
        channel = jump_transport.open_channel("direct-tcpip", dest_addr, local_addr)

        # ~~~ SSH into the VM ~~~
        vm_client = paramiko.SSHClient()
        vm_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.logger.debug(f"Connecting to VM {host} as {self.username} with {self.identity_file}")
        vm_client.connect(
            host,
            username=self.username,
            key_filename=key_path,
            sock=channel,
            allow_agent=True,
            look_for_keys=True,
        )
        self.logger.debug(f"Executing command: {command}")
        stdin, stdout, stderr = vm_client.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        error = stderr.read().decode()
        if exit_status != 0:
            self.logger.error(f"Error executing command {command} on {host} (code {exit_status}): {error}")
            raise RuntimeError(f"Error executing command {command} on {host}: {error}")
        if error:
            self.logger.warning(f"Command {command} on {host} wrote to stderr: {error}")
        self.logger.debug(f"Command output: {output}")
        vm_client.close()
        jump_client.close()
        return output.strip()
        