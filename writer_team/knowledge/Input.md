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

#### Master Node Setup

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

#### Worker Node Setup

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

## Why the Hybrid Approach is Recommended for Your Scenario

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

===
This is a fantastic, well-structured project! You’re already following best practices for reproducibility and automation. Your **main question** is about the **runtime configuration phase**: How to configure the VMs (especially the Kubernetes cluster) after they have been provisioned, given that some parameters (like master IP) are only known at runtime.

Let’s break down the solution space and provide concrete recommendations.

---

## 1. **Nix and Runtime Configuration: Limitations**

- **Nix** is fundamentally a **build-time** system; it produces immutable images. It’s **not designed for runtime configuration** where parameters are only known after provisioning (e.g., the master node's IP).
- **NixOS modules** can take parameters, but these must be known at image build time. You can’t easily “inject” the master IP after boot unless you rebuild and reprovision the image, which is slow and inflexible.

---

## 2. **Runtime Configuration Patterns**

### A. **Cloud-Init / Ignition**

- These are standard in the cloud world for “first boot” configuration. NixOS supports [cloud-init](https://search.nixos.org/options?channel=23.11&show=services.cloud-init.enable&from=0&size=50&sort=relevance&type=packages&query=cloud-init) and [Ignition](https://nixos.org/manual/nixos/stable/options.html#opt-systemd.services.ignition-setup.enable) out of the box.
- You can build a **generic image** with Nix, then inject a per-VM config at boot via cloud-init (user-data).
- **Pros:** Declarative, reproducible, integrates with most cloud/VM environments.
- **Cons:** Somewhat less flexible for complex orchestration than Ansible/Python.

### B. **SSH-based Scripting (Python, Bash, Ansible)**

- After provisioning, you use your orchestrator (Python) to SSH into the VMs and run commands/scripts to complete configuration.
- This is what you’re already starting to do (see your `provision_k8s_master` and `provision_k8s_worker`).
- **Pros:** Maximum flexibility, can react to runtime-discovered network info, etc.
- **Cons:** Slightly more imperative, but can be made robust.

---

## 3. **Recommended Approach For Your Use Case**

### **a) Build Minimal, Pre-Installed Images With Nix**

- Preinstall **Kubernetes (kubeadm, kubelet, kubectl)** and dependencies, but **do not configure/join the cluster at image build time**.
- Use your existing NixOS modules for this (as you already do).

### **b) Provision VMs & Discover IPs**

- Use your Python/libvirt provisioning to launch the VMs and **capture their IP addresses**.

### **c) Generate Per-Node Configs/Join Commands**

- On the master node, run `kubeadm init` via SSH.
- Extract the `kubeadm join ...` command (as you do).
- For each worker, SSH in and run the join command.

### **d) Optionally: Use Cloud-Init For Some Tasks**

- If you want to avoid SSH for initial setup, you can pass a cloud-init user-data file at VM creation with commands/scripts to run at first boot (e.g., a shell script that runs `kubeadm join ...` fetched from your orchestrator).

### **e) Automate Network Configuration**

- Use libvirt network XML to set up a predictable subnet, or have your Python code assign static IPs (if needed).
- Optionally, pass the master’s IP to worker nodes via cloud-init, or via your SSH script.

---

## 4. **Example: SSH-based Runtime Configuration Flow**

Here’s a high-level flow, matching your current architecture:

1. **Build image with Nix** (preinstalled k8s, but cluster not initialized).
2. **Provision master VM**. Wait for SSH to be available.
3. **SSH into master** and run:

   ```bash
   sudo kubeadm init --apiserver-advertise-address=<master_ip> --pod-network-cidr=10.244.0.0/16
   ```

   - Extract the `kubeadm join ...` command from the output.
4. **SSH into each worker** and run:

   ```bash
   sudo <kubeadm join ...>
   ```

5. **(Optional)**: Use cloud-init to run these steps automatically, by writing the commands to user-data at VM creation time.

---

## 5. **Why Not Use Only Nix?**

- Nix is not designed to “react” to runtime-discovered data like IP addresses or tokens. You’d need to rebuild the image for every cluster instance, which is slow and defeats the point of dynamic provisioning.
- Runtime configuration via SSH or cloud-init is the standard solution for this class of problem, even in NixOS-based systems.

---

## 6. **Alternatives: Ansible, etc.**

- If your runtime config becomes more complex, consider using [Ansible](https://nixos.org/manual/nixos/stable/#sec-ansible) (which works fine with NixOS) for the runtime phase.
- But for your current needs, **Python + SSH is sufficient and flexible**.

---

## 7. **Network Configuration: Master IP**

- If you want a **static master IP**, assign it via libvirt network XML or cloud-init network config.
- Otherwise, **discover the master IP** after boot (your code already does this), then pass it to workers (via SSH or cloud-init).

---

## 8. **Summary Table**

| Phase              | Tool/Method         | Recommendation                |
|--------------------|--------------------|-------------------------------|
| Image build        | NixOS Flakes       | Preinstall, no runtime config |
| Provisioning       | Python + libvirt   | As you do now                 |
| Runtime config     | Python+SSH, cloud-init | SSH scripts/cloud-init for kubeadm |
| Network config     | libvirt, cloud-init | Static or dynamic, as above   |

---

## 9. **Concrete Example: cloud-init for Worker Join**

Suppose you want to use **cloud-init** for the worker join step:

- After provisioning master, your orchestrator discovers the join command.
- When provisioning each worker, you generate a cloud-init user-data file like:

  ```yaml
  #cloud-config
  runcmd:
    - [ bash, -c, "sudo <kubeadm join ...>" ]
  ```

- Pass this user-data to the VM at creation time.
- This is supported by libvirt and NixOS.

---

## 10. **References**

- [NixOS + cloud-init](https://nixos.wiki/wiki/Cloud-init)
- [NixOS + Kubernetes](https://nixos.wiki/wiki/Kubernetes)
- [NixOS + Ansible](https://nixos.org/manual/nixos/stable/#sec-ansible)
- [Libvirt cloud-init docs](https://libvirt.org/formatdomain.html#cloud-init)
- [NixOS: runtime configuration pattern](https://discourse.nixos.org/t/first-boot-initialization-cloud-init-ignition-etc/10694)

---

## 11. **Sample Implementation Sketch**

**Python Orchestrator (pseudo-code):**

```python
# 1. Provision master, get IP
master_ip = provision_vm('master')
run_ssh(master_ip, 'sudo kubeadm init ...')
join_cmd = extract_kubeadm_join(master_ip)

# 2. Provision workers, pass join_cmd
for worker in workers:
    worker_ip = provision_vm(worker)
    run_ssh(worker_ip, f'sudo {join_cmd}')
```

**OR with cloud-init:**

- For each worker, generate a cloud-init file with the join command, pass at VM creation.

---

## 12. **Conclusion**

- **Continue with your current strategy:** Nix for build, Python/libvirt for provisioning, Python+SSH (or cloud-init) for runtime config.
- **Don’t try to force everything into Nix;** use the right tool for the right phase.
- **If you want full declarative first-boot config,** look into cloud-init, but SSH scripting is perfectly fine and flexible.

---

**If you want a minimal working example for cloud-init with NixOS, or a more robust SSH-based runtime config script, just ask!**

---

**In summary:**  
> Use Nix for immutable base images, Python/libvirt for provisioning, and Python+SSH or cloud-init for runtime configuration. Don’t try to force runtime (dynamic) config into Nix; use the orchestration layer to inject the actual parameters (master IP, join token, etc) at boot or just after boot. This is the standard, robust approach for reproducible, automated clusters.

---

Let me know if you want code snippets for a specific step
===
