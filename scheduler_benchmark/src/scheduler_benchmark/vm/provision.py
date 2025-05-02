from scheduler_benchmark.models import NodeConfig, HPCConfig, ClusterConfig
from scheduler_benchmark.vm.libvirt_helper import LibvirtConnection
import paramiko
import time
import logging
import functools
import socket
import os


def wait_for_ssh_ready(ip_arg_index=0, timeout=90, initial_interval=1, max_interval=10, logger=None):
    """
    Decorator to wait for SSH port 22 to be open before executing the function.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            host = args[ip_arg_index]
            log = logger or logging.getLogger(func.__module__)
            log.debug(f"Waiting for SSH on {host} (timeout={timeout}s)...")
            start = time.time()
            interval = initial_interval
            while time.time() - start < timeout:
                try:
                    # Try to resolve host to IP (for hostnames)
                    ip = socket.gethostbyname(host)
                    with socket.create_connection((ip, 22), timeout=2):
                        log.info(f"SSH port open on {host}")
                        break
                except Exception:
                    time.sleep(interval)
                    interval = min(max_interval, interval * 2)
            else:
                log.error(f"Timeout: SSH port not open on {host} after {timeout}s.")
                raise TimeoutError(f"SSH port not open on {host} after {timeout}s.")
            return func(*args, **kwargs)
        return wrapper
    return decorator

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

    @wait_for_ssh_ready(ip_arg_index=1, timeout=90, initial_interval=1, max_interval=10, logger=logging.getLogger(__name__))
    def ssh_execute(self, host, command):
        """
        SSH into the host and execute a command.
        Uses SSH config for ProxyJump etc.
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Use SSH config for jump etc.
        ssh_config = paramiko.SSHConfig()
        with open(os.path.expanduser("~/.ssh/config")) as f:
            ssh_config.parse(f)
        host_conf = ssh_config.lookup(host)
        hostname = host_conf.get('hostname', host)
        username = host_conf.get('user', self.username)
        identityfile = host_conf.get('identityfile', [self.identity_file])[0]

        ssh.connect(
            hostname=hostname,
            username=username,
            key_filename=identityfile,
            allow_agent=True,
            look_for_keys=True,
        )
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        ssh.close()
        return output.strip()
    

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
        worker_ips = [self.provision_node(wn) for wn in cluster.compute_nodes]

        try:
            self.ssh_execute(master_ip, "true")
        except Exception:
            self.logger.error(f"Master SSH not ready: {master_ip}")
            raise RuntimeError("Master SSH not ready")

        join_k8s_token = self.ssh_execute(master_ip, "sudo cat /var/lib/kubernetes/secrets/apitoken.secret")
        self.logger.info(f"Token: {join_k8s_token}")

        for ip in worker_ips:
            try:
                self.ssh_execute(ip, "true")
            except Exception:
                self.logger.error(f"Worker SSH not ready: {ip}")
                raise RuntimeError("Worker SSH not ready")

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
