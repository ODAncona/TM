from scheduler_benchmark.models import NodeConfig, HPCConfig, ClusterConfig
from scheduler_benchmark.vm.libvirt_helper import LibvirtConnection
import paramiko
import time


class VMProvisioner:
    def __init__(
        self,
        hostname: str,
        username: str | None = None,
        identity_file: str | None = None,
        pool_name: str = "default",
    ):
        self.hostname = hostname
        self.username = username
        self.identity_file = identity_file
        self.pool_name = pool_name

    def provision_node(
        self, node_config: NodeConfig, base_image: str | None = None
    ) -> str:
        """Provision a single node and return its IP address"""
        # Create VM using libvirt
        with LibvirtConnection(
            self.hostname, self.username, self.identity_file, self.pool_name
        ) as conn:
            domain, ip_address = conn.create_vm(node_config, base_image)
            if not ip_address:
                raise RuntimeError(
                    f"VM {node_config.name} did not obtain an IP"
                )

            return ip_address

    def ssh_execute(self, ip, command):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username="odancona", key_filename=self.identity_file)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        ssh.close()
        return output.strip()

    def provision_k8s_master(self, node: NodeConfig, base_image=None):
        master_ip = self.provision_node(node, base_image)
        time.sleep(60)  # Wait for node to boot fully

        join_command = self.ssh_execute(
            master_ip,
            "sudo kubeadm init --apiserver-advertise-address=$(hostname -I | awk '{print \$1}') --pod-network-cidr=10.244.0.0/16 | grep 'kubeadm join' -A1 | tr -d '\\n'",
        )

        # Setup kubeconfig for master user
        self.ssh_execute(
            master_ip,
            "mkdir -p $HOME/.kube && sudo cp -i /etc/kubernetes/admin.conf HOME/.kube/config && sudo chown (id -u):HOME/.kube/config",
        )
        return master_ip, join_command

    def provision_k8s_worker(
        self, node: NodeConfig, join_command, base_image=None
    ):
        worker_ip = self.provision_node(node, base_image)
        time.sleep(60)  # Wait for node to boot fully
        self.ssh_execute(worker_ip, f"sudo {join_command}")
        return worker_ip

    def provision_cluster(
        self, cluster: ClusterConfig, base_image: str | None = None
    ) -> dict[str, str]:
        """Provision an entire cluster from a cluster config"""
        ips = {}

        # Provision head nodes
        for node in cluster.head_nodes:
            ip = self.provision_node(node, base_image)
            ips[node.name] = ip

        # Provision compute nodes
        for node in cluster.compute_nodes:
            ip = self.provision_node(node, base_image)
            ips[node.name] = ip

        return ips

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
