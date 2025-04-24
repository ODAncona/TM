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

    def ssh_execute(self, ip, command):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username="odancona", key_filename=self.identity_file)
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


    def provision_k8s_cluster(self, cluster: ClusterConfig, pod_cidr="10.244.0.0/16"):

        master_config = cluster.head_nodes[0]
        worker_configs = cluster.compute_nodes

        # 1. Provision master node
        master_ip = self.provision_node(master_config)
        print(f"Master IP: {master_ip}")

        # 2. kubeadm init sur le master
        print("Initialisation du master K8s...")
        kubeadm_init_cmd = (
            f"sudo kubeadm init --apiserver-advertise-address={master_ip} --pod-network-cidr={pod_cidr}"
        )
        kubeadm_output = self.ssh_execute(master_ip, kubeadm_init_cmd)
        join_cmd = extract_join_command(kubeadm_output)
        print(f"Join command: {join_cmd}")

        # 3. Préparer le kubeconfig sur le master pour l'utilisateur
        self.ssh_execute(
            master_ip,
            "mkdir -p $HOME/.kube && "
            "sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config && "
            "sudo chown $(id -u):$(id -g) $HOME/.kube/config"
        )

        # 4. Appliquer le CNI (ex: flannel)
        print("Application du CNI flannel...")
        self.ssh_execute(
            master_ip,
            "kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml"
        )

        # 5. Provision et join des workers
        for worker_conf in worker_configs:
            worker_ip = self.provision_node(worker_conf)
            print(f"Provisionnement worker: {worker_conf.name} ({worker_ip})")
            # Attendre que le worker soit bien up
            time.sleep(30)
            print(f"Join {worker_conf.name} au cluster...")
            self.ssh_execute(worker_ip, f"sudo {join_cmd}")

        # 6. Vérification finale
        print("Vérification des nœuds K8s...")
        time.sleep(30)
        nodes = self.ssh_execute(master_ip, "kubectl get nodes -o wide")
        print(nodes)
        return master_ip


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
