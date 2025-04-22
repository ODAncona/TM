You've already built a solid foundation by leveraging Nix flakes for deterministic VM images, Hydra for configuration management, and Python with libvirt for provisioning. The key challenge you're facing now is how to handle runtime configuration dynamically, specifically:

- Dynamically discovering IP addresses at runtime.
- Configuring Kubernetes clusters (or other schedulers) dynamically after VM boot.

Here's a structured recommendation for your runtime configuration:

---

## 1. Runtime Configuration Approach

You have several options for runtime configuration:

- **Option 1: Pure NixOS (Dynamic NixOS Configurations via SSH)**
- **Option 2: Imperative Configuration (Ansible, Python SSH scripts)**
- **Option 3: Hybrid Approach (Recommended)**

Given your existing setup and your need to dynamically discover IP addresses and configure schedulers at runtime, a hybrid approach is ideal:

- **Build immutable VM images with Nix** (pre-installed packages, kernel, Kubernetes binaries, etc.).
- **Use Python scripts for minimal imperative runtime configuration** (IP discovery, joining nodes to clusters, dynamic parameters).

---

## 2. Recommended Hybrid Approach

### Step A: Immutable Image (NixOS)

- Pre-install Kubernetes binaries, container runtimes (containerd, CRI-O), Volcano scheduler binaries, and required system tools via Nix flakes.
- Include a simple NixOS configuration that sets up Kubernetes components but without runtime-specific parameters (like master IP).

### Step B: Imperative Runtime Configuration Script (Python + SSH)

- Use your existing Python libvirt wrapper to provision VMs and discover IP addresses.
- After provisioning, use Python with SSH (Paramiko or Fabric) to run imperative commands to configure the cluster dynamically, such as:
  - Running `kubeadm init` on the master node.
  - Retrieving the `kubeadm join` token and command.
  - Executing `kubeadm join` on worker nodes.

The key here is to leverage Kubernetes' built-in cluster bootstrap workflow (`kubeadm`) rather than trying to preconfigure everything statically.

---

## 3. Concrete Implementation Steps

Here's how you can practically implement this:

### ✅ Step 1: Update your NixOS Image (VM Image Layer)

Modify your `flake.nix` and Kubernetes modules to:

- Install Kubernetes and container runtime packages.
- Enable required services (containerd, kubelet), but **do not configure the master IP statically**.

Example (`modules/kubernetes/base.nix`):

```nix
{ config, lib, pkgs, ... }:

{
  environment.systemPackages = with pkgs; [
    kubectl
    kubeadm
    kubelet
    containerd
  ];

  services.containerd.enable = true;

  systemd.services.kubelet = {
    enable = true;
    wantedBy = [ "multi-user.target" ];
  };

  networking.firewall.enable = true;
  networking.firewall.allowedTCPPorts = [
    22      # SSH
    6443    # Kubernetes API Server (master node)
    2379    # etcd server client API (master node)
    2380    # etcd peer communication (master node)
    10250   # Kubelet API (all nodes)
  ];
  networking.firewall.allowedTCPPortRanges = [
    { from = 30000; to = 32767; }  # NodePort services
  ];
}
```

### ✅ Step 2: Python Orchestration (Runtime Layer)

In your Python provisioning scripts (`provision.py`), after creating the VMs and obtaining their IPs, use SSH to configure Kubernetes dynamically:

#### Master Node Setup:

```python
def setup_k8s_master(self, master_ip):
    init_cmd = (
        "sudo kubeadm init "
        "--apiserver-advertise-address=$(hostname -I | awk '{print $1}') "
        "--pod-network-cidr=10.244.0.0/16 "
        "--ignore-preflight-errors=Swap"
    )
    output = self.ssh_execute(master_ip, init_cmd)

    # Extract join command from output
    join_command = self.ssh_execute(
        master_ip, 
        "kubeadm token create --print-join-command"
    )

    # Setup kubeconfig for user
    self.ssh_execute(
        master_ip,
        "mkdir -p $HOME/.kube && "
        "sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config && "
        "sudo chown $(id -u):$(id -g) $HOME/.kube/config"
    )

    # Install a network plugin (e.g., Flannel or Calico)
    self.ssh_execute(
        master_ip,
        "kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml"
    )

    return join_command
```

#### Worker Node Setup:

```python
def setup_k8s_worker(self, worker_ip, join_command):
    self.ssh_execute(worker_ip, f"sudo {join_command} --ignore-preflight-errors=Swap")
```

### ✅ Step 3: Integrate into your Hydra-based workflow

In your main Hydra workflow (`main.py`):

```python
# Provision master node
master_node_config = config.cluster.head_nodes[0]
master_ip = provisioner.provision_node(master_node_config, base_image)

# Setup Kubernetes master
join_command = provisioner.setup_k8s_master(master_ip)

# Provision and setup worker nodes
for worker_node in config.cluster.compute_nodes:
    worker_ip = provisioner.provision_node(worker_node, base_image)
    provisioner.setup_k8s_worker(worker_ip, join_command)
```

---

## 4. Benefits of this Approach

- **Declarative Images**: You maintain reproducibility and immutability by using Nix flakes for VM images.
- **Dynamic Runtime Configuration**: Python scripts handle runtime-specific parameters (IP addresses, join commands) efficiently.
- **Simplicity and Maintainability**: Leverages Kubernetes' well-tested bootstrap methods (`kubeadm`), reducing complexity and potential errors.
- **Flexibility**: Easy to adapt to other schedulers (SLURM, Flux) by providing analogous runtime configuration scripts.

---

## 5. Alternative Approaches (Less Recommended)

- **Pure Nix Runtime Configuration**: Nix is declarative and not ideal for imperative operations like discovering dynamic IPs at runtime. It would require complex workarounds (e.g., custom activation scripts, NixOps, or custom Nix store manipulations).
- **Ansible or SaltStack**: Good alternatives, but given your existing Python/libvirt workflow, adding another tool might introduce unnecessary complexity.

---

## 6. Final Recommendation

✅ **Hybrid Approach** (Immutable NixOS images + Python-based imperative runtime configuration) is the most straightforward and maintainable solution given your existing stack and requirements.

This approach allows you to leverage the strengths of both declarative configuration (Nix) and imperative runtime flexibility (Python scripts), ensuring you have a robust, reproducible, and maintainable HPC benchmarking platform.


===

## Comparatif

---
Let's perform a structured comparative analysis between the main approaches relevant to your scenario:

- **Approach A: Pure NixOS (NixOps, Colmena)**
- **Approach B: Imperative (Ansible, Python SSH scripts)**
- **Approach C: Hybrid Approach (Immutable NixOS + Python SSH scripts)** *(previously recommended)*

We'll evaluate these approaches against several important criteria:

| Criteria                        | Pure NixOS (Colmena/NixOps) 🐝 | Imperative (Ansible/Python SSH) 🐍 | Hybrid (Immutable NixOS + Python SSH) 🚀 |
|---------------------------------|--------------------------------|------------------------------------|------------------------------------------|
| **Declarative Configuration**   | ✅ Fully Declarative           | ❌ Imperative                      | ✅ Declarative images + imperative runtime |
| **Dynamic Runtime Flexibility** | ⚠️ Limited flexibility        | ✅ Highly dynamic and flexible     | ✅ Highly dynamic and flexible           |
| **Reproducibility**             | ✅ Excellent                   | ⚠️ Depends on discipline          | ✅ Excellent (due to immutable images)   |
| **Complexity**                  | ⚠️ Moderate (learning curve)  | ✅ Low (easy to understand)       | ✅ Moderate (balanced)                   |
| **Community & Ecosystem**       | ⚠️ Smaller but growing        | ✅ Large (Ansible, Python)        | ✅ Good (leverages both ecosystems)      |
| **Integration with Existing Stack (Hydra+Python+Libvirt)** | ⚠️ Moderate integration effort | ✅ Easy integration (already Python-based) | ✅ Easy integration (already Python-based) |
| **Observability & Debugging**   | ⚠️ Moderate                   | ✅ Easy (imperative scripts)      | ✅ Easy (imperative runtime)             |
| **Idempotency & Robustness**    | ✅ Strong                      | ⚠️ Depends on implementation      | ✅ Good (immutable infrastructure)       |
| **Maintenance & Extensibility** | ✅ Good                        | ⚠️ Moderate (imperative drift)    | ✅ Excellent (clear separation of concerns) |

---

## Approach A: Pure NixOS (Colmena/NixOps) 🐝

**Description:**
- Colmena is a declarative NixOS deployment tool that allows you to manage multiple NixOS hosts declaratively.
- NixOps is another declarative deployment tool, but less actively maintained recently compared to Colmena.

**Strengths:**
- Fully declarative, reproducible infrastructure.
- Excellent Nix integration, leveraging Nix ecosystem for configuration management.
- Good reproducibility and rollback support.

**Weaknesses:**
- Limited dynamic runtime flexibility. It's challenging to dynamically discover IP addresses or runtime parameters because Nix/Colmena expects static, declarative inputs.
- More complexity and higher entry barrier for newcomers.
- Smaller community compared to Ansible or Python-based tooling.

**When to use:**
- If your infrastructure is static or has predictable runtime parameters.
- When fully declarative management is a strict requirement.

**When to avoid:**
- Highly dynamic runtime configurations (like dynamically discovering IP addresses, joining clusters at runtime).
- When you need a lot of imperative logic (e.g., conditional runtime logic).

---

## Approach B: Imperative (Ansible/Python SSH scripts) 🐍

**Description:**
- Ansible or Python scripts directly SSH into hosts to configure them imperatively.
- Highly flexible and dynamic, but less declarative.

**Strengths:**
- Highly dynamic and flexible, ideal for runtime discovery of IP addresses, tokens, and dynamic cluster joins.
- Easy to understand, debug, and maintain for developers familiar with Python or Ansible.
- Large community, extensive ecosystem, and many existing modules.

**Weaknesses:**
- Imperative scripts can drift over time (less reproducible).
- Reproducibility depends on developer discipline (version control, careful scripting).
- Potentially lower robustness and idempotency unless carefully implemented.

**When to use:**
- Highly dynamic environments, with frequent runtime changes.
- Teams familiar with Python or Ansible, wanting rapid iteration and flexibility.

**When to avoid:**
- When reproducibility and immutability are critical.
- When drift and configuration management complexity are major concerns.

---

## Approach C: Hybrid Approach (Immutable NixOS + Python SSH scripts) 🚀 *(Recommended)*

**Description:**
- Immutable NixOS images built with Nix flakes (fully declarative, reproducible).
- Python-based SSH scripts for dynamic runtime configuration (joining Kubernetes clusters, dynamic IP discovery).

**Strengths:**
- Combines declarative reproducibility (immutable images) with imperative flexibility (Python scripts).
- Easy integration with your existing Python+Hydra+Libvirt stack.
- Clear separation of concerns: declarative base infrastructure, imperative runtime configuration.
- Good observability, debugging, and maintenance.
- Excellent balance between reproducibility, robustness, and flexibility.

**Weaknesses:**
- Slightly increased complexity due to two separate tooling layers (Nix + Python).
- Requires discipline to clearly define boundaries between declarative and imperative layers.

**When to use:**
- When you need both reproducibility and dynamic runtime flexibility.
- When you already have or prefer Python scripting skills and ecosystem.
- Ideal for Kubernetes clusters, HPC clusters, and dynamic runtime configuration scenarios.

**When to avoid:**
- Extremely simple deployments that don't justify two layers.
- Purely static infrastructure with no runtime dynamics (pure NixOS might be simpler).

---

## Why the Hybrid Approach is Recommended for Your Scenario:

Your scenario specifically involves:

- Dynamic IP discovery at runtime (libvirt DHCP leases).
- Dynamic Kubernetes cluster bootstrap (master IP, join commands).
- Existing familiarity with Python, Hydra, and libvirt.
- Strong reproducibility requirements for benchmarking experiments.

The hybrid approach perfectly matches these needs by:

- Leveraging NixOS flakes for reproducibility and immutability of VM images.
- Using Python scripts for dynamic runtime configuration (Kubernetes cluster joins, IP discovery).
- Clearly separating concerns, allowing easy debugging and maintenance.
- Integrating seamlessly with your existing Python/Hydra-based orchestration stack.

---

## Final Recommendation: 🚀 Hybrid Approach (Immutable NixOS + Python SSH) 🚀

Given your specific scenario, existing stack, and requirements, the hybrid approach provides the best balance between reproducibility, flexibility, maintainability, and ease of integration.

Colmena (pure NixOS declarative approach) is elegant and powerful, but its limited dynamic flexibility at runtime makes it less suitable for your highly dynamic runtime configuration needs.

The imperative-only approach (pure Python/Ansible) is highly flexible but sacrifices some reproducibility and immutability guarantees that are critical for your benchmarking experiments.

Thus, the hybrid approach (immutable NixOS images + Python runtime scripts) is the most suitable, practical, and balanced solution for your scenario.