Let's clearly analyze and summarize your current situation and available technologies to make an informed choice.

## 🚩 Your Current Setup and Requirements

- **VM Image**: Built with NixOS (immutable, reproducible, using `nixos-generators`).
- **Provisioning**: Custom Python script using libvirt (dynamic VM creation, disk management, IP discovery).
- **Runtime Configuration**: Currently unclear and the main question. You need to:
  - Initialize Kubernetes (`kubeadm init`) on the master node.
  - Dynamically discover the master node IP.
  - Join worker nodes to the Kubernetes cluster (`kubeadm join`).

---

## 📌 Analysis of Technologies for Runtime Configuration

Let's evaluate each option clearly:

### 1. **Nix / NixOS (Colmena, Morph, NixOps)**

**Pros:**
- Declarative, reproducible, consistent with your existing Nix-based setup.
- Colmena, Morph, or NixOps can manage multiple NixOS hosts declaratively.

**Cons:**
- Not ideal for highly dynamic runtime configuration (e.g., dynamic IP discovery, kubeadm tokens).
- Nix evaluates everything upfront. Runtime data (IP addresses, tokens) is unknown at build-time, making Nix a poor fit for this dynamic step.
- Colmena and Morph are great for static cluster definitions but not ideal for dynamic cluster bootstrap logic.

**Conclusion:**  
❌ Not ideal for dynamic cluster bootstrap. Use Nix for the immutable image generation, but avoid it for dynamic runtime configuration.

---

### 2. **Ansible**

**Pros:**
- Mature, widely adopted, and specifically designed for dynamic runtime configuration.
- Can easily handle dynamic discovery of IP addresses, tokens, and conditional logic.
- Idempotent, easy to debug, and maintainable.

**Cons:**
- Adds another tool to your stack (but very common and lightweight).
- Slightly imperative approach (but still idempotent and declarative to an extent).

**Conclusion:**  
✅ Highly recommended. Ansible is a proven solution for exactly this scenario.

---

### 3. **Custom Python Script**

**Pros:**
- Fits naturally with your existing Python-based libvirt provisioning.
- Full flexibility to code exactly what you need.

**Cons:**
- Reinventing the wheel: You must manually handle idempotency, error handling, retries, SSH connections, etc.
- Can quickly become complex and hard to maintain.

**Conclusion:**  
⚠️ Possible, but not recommended. Only pick this if you have very specific custom logic that Ansible can't handle (unlikely).

---

### 4. **Bash Script**

**Pros:**
- Simple for quick prototyping.
- Easy to integrate and debug manually.

**Cons:**
- Error-prone, hard to maintain at scale.
- Not idempotent by default, requires manual management of state and retries.

**Conclusion:**  
⚠️ Possible for small setups. Not recommended for long-term maintainability or complexity.

---

### 5. **Terraform/OpenTofu**

**Pros:**
- Declarative infrastructure management.
- Some providers can handle dynamic runtime configuration.

**Cons:**
- Terraform/OpenTofu is great for provisioning resources, but less ideal for runtime cluster configuration (like kubeadm init/join).
- The libvirt provider is not reliable in your experience.

**Conclusion:**  
❌ Not suitable for dynamic Kubernetes cluster bootstrapping.

---

## 🥇 Recommended Approach

Given your scenario and analysis above, the best-practice approach is:

| Step                              | Recommended Tool                  | Reasoning                            |
| --------------------------------- | --------------------------------- | ------------------------------------ |
| **VM Image Generation**           | ✅ Nix (`nixos-generators`)        | Immutable, reproducible, consistent  |
| **Provisioning (libvirt)**        | ✅ Custom Python script (existing) | Already working, flexible            |
| **Dynamic Runtime Configuration** | ✅ Ansible                         | Mature, idempotent, easy to maintain |
| **Application Deployment**        | ✅ Kubernetes manifests / Helm     | Kubernetes native                    |

---

## 🚀 Suggested Workflow (Concrete Steps)

Here's a practical workflow you can follow:

### 1. **VM Image (NixOS)**

- Build your VM images with Kubernetes tools pre-installed (kubeadm, kubelet, kubectl).
- No runtime-specific configuration (like IP addresses or tokens) at this stage.

### 2. **Provision VMs (Python libvirt script)**

- Launch VMs with libvirt.
- Discover VM IP addresses dynamically (already implemented in your Python script).

### 3. **Dynamic Kubernetes Setup (Ansible)**

- Write an Ansible playbook that:
  - Connects via SSH to the master node.
  - Runs `kubeadm init` and captures the join token and discovery hash.
  - Connects to worker nodes and runs `kubeadm join` using the captured data.
  - Installs a CNI network plugin (e.g., Calico, Flannel) on the master node.

Example minimal Ansible structure:

```yaml
- hosts: master
  become: true
  tasks:
    - name: Initialize Kubernetes master
      command: kubeadm init --pod-network-cidr=10.244.0.0/16
      args:
        creates: /etc/kubernetes/admin.conf
      register: kubeadm_init

    - name: Save kubeconfig for admin user
      command: "{{ item }}"
      with_items:
        - mkdir -p /home/admin/.kube
        - cp -i /etc/kubernetes/admin.conf /home/admin/.kube/config
        - chown admin:admin /home/admin/.kube/config

    - name: Install CNI plugin (example: Flannel)
      become_user: admin
      command: kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml

- hosts: workers
  become: true
  tasks:
    - name: Join Kubernetes cluster
      command: "{{ hostvars['master'].kubeadm_init.stdout_lines | select('match', 'kubeadm join.*') | first }}"
      args:
        creates: /etc/kubernetes/kubelet.conf
```

### 4. **Application Deployment (Helm/Kustomize)**

- Use Kubernetes-native tools (Helm charts or Kustomize overlays) to deploy your workloads.

---

## 🎯 Final Recommendation

✅ **Use Ansible for dynamic runtime cluster configuration.**  
This is the most straightforward, maintainable, and robust choice for your scenario.

**Final Stack:**
- NixOS (`nixos-generators`) → Python libvirt script → Ansible → Kubernetes manifests / Helm

---

## 📚 Final Thoughts

- Keep NixOS for immutable OS images.
- Leverage your existing Python libvirt script for provisioning VMs.
- Use Ansible for runtime dynamic configuration (init/join Kubernetes nodes).
- Deploy apps using Kubernetes-native tooling (kubectl, Helm, Kustomize).

This combination is widely adopted, flexible, maintainable, and well-aligned with your existing tooling and workflow.