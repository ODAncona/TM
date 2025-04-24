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

Let me know if you want code snippets for a specific step!