Here's a straightforward guide on setting up a Kubernetes (K8s) cluster with one master and four worker nodes using 5 virtual machines (VMs). This assumes you're using Ubuntu/Debian-based Linux distributions, but the steps are similar for other distributions.

## Prerequisites

- 5 virtual machines (VMs) running Linux (Ubuntu/Debian recommended)
- At least 2 CPU cores and 2GB RAM per node (more recommended)
- SSH access and sudo privileges
- Unique hostname and static IP addresses for each VM
- Network connectivity between nodes
- Disable swap memory (required by Kubernetes)

---

## Step-by-Step Installation Guide:

### Step 1: Prepare Your Nodes (All Nodes)

1. **Set Hostnames and Hosts File:**

On each node, set a unique hostname:

bash

Copy code

`sudo hostnamectl set-hostname master-node # worker nodes: sudo hostnamectl set-hostname worker-node1 sudo hostnamectl set-hostname worker-node2 sudo hostnamectl set-hostname worker-node3 sudo hostnamectl set-hostname worker-node4`

Edit `/etc/hosts` on all nodes and add entries for each node (replace IP addresses with your actual IPs):

bash

Copy code

`sudo nano /etc/hosts`

Example:

text

Copy code

`192.168.1.10 master-node 192.168.1.11 worker-node1 192.168.1.12 worker-node2 192.168.1.13 worker-node3 192.168.1.14 worker-node4`

2. **Disable Swap (required by Kubernetes):**

bash

Copy code

`sudo swapoff -a sudo sed -i '/ swap / s/^/#/' /etc/fstab`

3. **Allow firewall rules (if firewall active):**

bash

Copy code

`sudo ufw allow ssh sudo ufw allow 6443/tcp # Kubernetes API Server sudo ufw allow 2379:2380/tcp # etcd server client API sudo ufw allow 10250/tcp # Kubelet API sudo ufw allow 10251/tcp # kube-scheduler sudo ufw allow 10252/tcp # kube-controller-manager sudo ufw allow 30000:32767/tcp # NodePort services sudo ufw reload`

4. **Enable Kernel Modules and Networking:**

bash

Copy code

`sudo modprobe overlay sudo modprobe br_netfilter  # Persist modules on reboot cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf overlay br_netfilter EOF  # Set system settings required by Kubernetes cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf net.bridge.bridge-nf-call-ip6tables = 1 net.bridge.bridge-nf-call-iptables = 1 net.ipv4.ip_forward = 1 EOF  sudo sysctl --system`

---

### Step 2: Install Docker Container Runtime (All Nodes):

bash

Copy code

`sudo apt update sudo apt install -y apt-transport-https ca-certificates curl software-properties-common  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg  echo \   "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \   https://download.docker.com/linux/ubuntu \   $(lsb_release -cs) stable" | \   sudo tee /etc/apt/sources.list.d/docker.list  sudo apt update sudo apt install -y docker-ce docker-ce-cli containerd.io  # Configure Docker daemon to use systemd as cgroup driver cat <<EOF | sudo tee /etc/docker/daemon.json {   "exec-opts": ["native.cgroupdriver=systemd"],   "log-driver": "json-file",   "log-opts": {     "max-size": "100m"   },   "storage-driver": "overlay2" } EOF  sudo systemctl restart docker sudo systemctl enable docker`

---

### Step 3: Install Kubernetes Components (All Nodes):

bash

Copy code

`sudo apt update && sudo apt install -y apt-transport-https curl  curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | sudo gpg --dearmor -o /usr/share/keyrings/kubernetes-archive-keyring.gpg  echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /" | sudo tee /etc/apt/sources.list.d/kubernetes.list  sudo apt update sudo apt install -y kubelet kubeadm kubectl sudo apt-mark hold kubelet kubeadm kubectl`

---

### Step 4: Initialize Kubernetes Cluster (Master Node Only):

On the master node, run:

bash

Copy code

`sudo kubeadm init --pod-network-cidr=10.244.0.0/16`

Once completed, follow the instructions provided by kubeadm to set up your kubeconfig:

bash

Copy code

`mkdir -p $HOME/.kube sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config sudo chown $(id -u):$(id -g) $HOME/.kube/config`

---

### Step 5: Install Network Plugin (Master Node Only):

For example, using Flannel:

bash

Copy code

`kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml`

---

### Step 6: Join Worker Nodes to Cluster (Worker Nodes Only):

On each worker node, run the join command generated from the master node's `kubeadm init` command. It looks something like this:

bash

Copy code

`sudo kubeadm join <MASTER_IP>:6443 --token <TOKEN> \   --discovery-token-ca-cert-hash sha256:<HASH>`

If you lost your join command, you can regenerate it from the master node:

bash

Copy code

`kubeadm token create --print-join-command`

---

### Step 7: Verify the Cluster (Master Node):

bash

Copy code

`kubectl get nodes`

All nodes should display as `Ready` after a few minutes.

---

## Your Kubernetes cluster is now up and running!

You now have a single master node and four worker nodes configured. You can deploy workloads and manage your applications using Kubernetes resources.

### Next Steps (Optional):

- Install Kubernetes Dashboard for UI management.
- Configure persistent storage solutions.
- Deploy your applications using YAML manifests or Helm charts.

That's it! Your Kubernetes cluster is ready to use.