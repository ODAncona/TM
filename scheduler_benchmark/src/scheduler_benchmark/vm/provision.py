from scheduler_benchmark.models import NodeConfig, HPCConfig, ClusterConfig
from scheduler_benchmark.vm.libvirt_helper import LibvirtConnection


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
        self, node: NodeConfig, base_image: str | None = None
    ) -> str:
        """Provision a single node and return its IP address"""
        # Create VM using libvirt
        with LibvirtConnection(
            self.hostname, self.username, self.identity_file, self.pool_name
        ) as conn:
            domain, ip_address = conn.create_vm(node, base_image)
            return ip_address

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
