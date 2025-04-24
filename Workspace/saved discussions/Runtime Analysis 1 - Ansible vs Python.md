Let's carefully analyze your current setup and the available options for runtime configuration.

# Your Current Setup

- **VM Image**: Built with Nix (immutable, reproducible)
- **Provisioning**: Custom Python script using libvirt (dynamic VM creation, disk management, IP discovery)
- **Runtime Configuration**: Currently unclear—this is your missing piece. You need to dynamically configure your Kubernetes cluster once your VMs are up and running.

# Key Requirements for Runtime Configuration

- Dynamically discover VM IP addresses after boot.
- Initialize Kubernetes master node (`kubeadm init`).
- Retrieve the join token and discovery hash from the master node.
- Use the join token to connect worker nodes (`kubeadm join`).
- Possibly configure additional Kubernetes resources (network plugin, storage, RBAC, etc.).

# Comparison of Available Technologies

Let's compare your options clearly:

| Option            | Complexity  | Flexibility | Maintainability | Integration with existing setup                        | Notes                                                                                                                 |
| ----------------- | ----------- | ----------- | --------------- | ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| **Python Script** | Medium-High | High        | Medium-Low      | High (already using Python for libvirt)                | Good if you prefer consistent tooling, but you must manually handle SSH connections, error handling, and idempotency. |
| **Bash Script**   | Medium      | Medium      | Low             | Medium (simple to integrate, but messy if logic grows) | Quick solution, but can become fragile and hard to maintain.                                                          |
| **Ansible**       | Medium      | High        | High            | Medium-High (well-suited for SSH-based provisioning)   | Idempotent, declarative, good for long-term maintenance, handles SSH, retries, error handling for you.                |

# Analysis of Each Option

### 1. Python Script

**Pros:**

- You already have Python code for VM provisioning.
- Easy integration with existing libvirt-based provisioning.
- Full control over logic.

**Cons:**

- Need to manually handle SSH connections, commands, error checking, retries, idempotency.
- More boilerplate and complexity as your logic grows.

### 2. Bash Script

**Pros:**

- Quick to write initially.
- Easy to debug interactively.

**Cons:**

- Fragile, especially as complexity increases.
- Difficult error handling, retries, idempotency.

### 3. Ansible

**Pros:**

- Declarative and idempotent, handles retries and error cases gracefully.
- SSH-based, matches your existing setup (you've already provisioned SSH keys).
- Mature ecosystem, widely used for Kubernetes bootstrapping.

**Cons:**

- Adds another tool to your stack if you're not currently using Ansible.

# Recommended Approach

Given your scenario, **Ansible** is the strongest choice:

- Your workflow already has SSH keys and known_hosts configured, ideal for Ansible.
- Ansible is specifically designed for dynamic runtime configuration tasks: SSH-based remote command execution, dynamic inventory (auto-discovery of IPs), idempotency, and error handling.
- Long-term maintainability is greatly improved compared to custom Python or Bash scripts.

# Suggested Architecture

Here's the recommended high-level flow:



```csharp
Nix (Immutable OS Image + kubeadm/kubelet installed)
    ↓
Python libvirt script (Provision VMs, get IP addresses)
    ↓
Ansible (Dynamic runtime configuration)
    ├── Master node: kubeadm init, retrieve join token/hash
    └── Worker nodes: kubeadm join using token/hash
    └── Install network plugin (e.g., Calico, Flannel)
    └── Additional cluster configuration (optional)
    ↓
Kubectl / Helm (Deploy application workloads on Kubernetes)
```

# Concrete Example (Ansible Playbook)

Minimal example of what your Ansible playbook would look like:

**inventory.ini (dynamic IPs provided by your Python script)**

```ini
[master]
master ansible_host=192.168.122.10

[workers]
worker1 ansible_host=192.168.122.11
worker2 ansible_host=192.168.122.12

[k8s_cluster:children]
master
workers
```

**playbook.yml**

```yaml
- hosts: master
  become: yes
  tasks:
    - name: Initialize Kubernetes Master
      command: kubeadm init --pod-network-cidr=10.244.0.0/16
      args:
        creates: /etc/kubernetes/admin.conf
      register: kubeadm_init

    - name: Set kubeconfig for root user
      shell: |
        mkdir -p $HOME/.kube
        cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
        chown $(id -u):$(id -g) $HOME/.kube/config

    - name: Install Pod Network (Flannel)
      command: kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
      environment:
        KUBECONFIG: /etc/kubernetes/admin.conf

    - name: Get join command
      shell: kubeadm token create --print-join-command
      register: join_command_raw

    - name: Save join command
      set_fact:
        join_command: "{{ join_command_raw.stdout }}"

- hosts: workers
  become: yes
  tasks:
    - name: Join workers to cluster
      command: "{{ hostvars['master'].join_command }}"
      args:
        creates: /etc/kubernetes/kubelet.conf
```


# Integration with your Python Script

Your Python libvirt script would:

- Provision VMs and wait until they report their IP addresses.
- Generate an Ansible inventory file dynamically (or pass IPs via a simple JSON/YAML file).
- Trigger the Ansible playbook (e.g., via subprocess call: `ansible-playbook -i inventory.ini playbook.yml`).

# Summary of Recommended Approach

✅ **Nix** for immutable VM images  
✅ **Python + libvirt** for dynamic VM provisioning  
✅ **Ansible** for dynamic runtime configuration (kubeadm init/join, network plugins, etc.)  
✅ **Kubectl/Helm** for deploying applications on Kubernetes

This approach provides you with an optimal balance between simplicity, maintainability, and flexibility—leveraging the strengths of each tool for its intended purpose.

Would you like me to help you outline how to integrate Ansible with your existing Python provisioning script, or clarify any part of this recommendation further?