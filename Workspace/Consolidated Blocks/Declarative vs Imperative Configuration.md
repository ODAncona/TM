

In traditional imperative infrastructure workflows, virtual machines (VMs) are provisioned first, and then operating systems are configured, software packages installed, and services configured sequentially through explicit commands or scripts. While straightforward, this approach often leads to configuration drift, inconsistent states across nodes, and reduced reproducibility, especially when scaling clusters or repeatedly running experiments. To mitigate these issues, our workflow adopts a declarative infrastructure approach leveraging Nix flakes to build deterministic, immutable VM images. At build time, we declaratively specify the entire OS configuration, including networking, DNS settings, required software packages, and Kubernetes components. This results in reproducible VM images that encapsulate the complete system state, significantly enhancing reliability, consistency, and ease of debugging. However, certain runtime-specific parameters, such as dynamically discovered IP addresses and Kubernetes node join tokens, cannot be embedded statically into these immutable images. Therefore, after provisioning these pre-built images, we perform minimal imperative runtime configuration using Python scripts: dynamically discovering IP addresses, initializing the Kubernetes master node, retrieving the required join token, and subsequently joining worker nodes to the cluster. This hybrid approach combines the strengths of declarative configuration—such as reproducibility, immutability, and consistency—with the flexibility and dynamic configuration capabilities of imperative scripting. By clearly separating static configuration (handled declaratively at build time) from runtime-specific dynamic configuration (handled imperatively at provision time), we achieve a robust, scalable, and maintainable infrastructure workflow, well-suited to iterative experimentation and rapid development cycles.

---
@startuml
title Traditional Imperative Infrastructure Workflow

actor Developer as dev

box "Provisioned VM (Blank)" #LightYellow
  participant "Provision VM (Empty)" as provision
  participant "Configure OS (SSH)" as os_config
  participant "Install Packages (SSH)" as pkg_install
  participant "Configure Software (SSH)" as sw_config
end box

dev -> provision : Provision new VM
provision -> os_config : Configure OS settings\n(Network, DNS, Hostname)
os_config -> pkg_install : Install software packages\n(e.g. Kubernetes, runtimes)
pkg_install -> sw_config : Configure installed software\n(Cluster setup, services)

note right of sw_config #FFDDCC
All steps imperative:\n
- Manual or scripted SSH commands\n
- Potential configuration drift\n
- Harder reproducibility
end note

@enduml

---
@startuml
title Hybrid Declarative-Imperative Infrastructure Workflow

actor Developer as dev

box "Declarative Build Phase (Immutable Image)" #LightGreen
  participant "Declarative OS Configuration (Nix flakes)" as nix_os
  participant "Declarative Package Installation (Nix flakes)" as nix_pkg
  participant "Declarative Software Configuration (Nix flakes)" as nix_sw
  database "Immutable VM Image" as image
end box

box "Imperative Provision Phase (Dynamic Runtime)" #LightBlue
  participant "Provision VM from Image" as provision
  participant "Dynamic Runtime Configuration (Python SSH)" as dyn_config
  participant "Run Experiment" as experiment
end box

dev -> nix_os : Define OS configuration\n(Network, DNS, Hostname template)
nix_os -> nix_pkg : Define software packages\n(Kubernetes, runtimes)
nix_pkg -> nix_sw : Define software configuration\n(Services, systemd)
nix_sw -> image : Build Immutable Image

dev -> provision : Provision VM using immutable image
image -> provision : VM boots from pre-built image
provision -> dyn_config : Dynamic configuration\n(IP discovery, kubeadm join)
dyn_config -> experiment : Infrastructure ready\n(run experiments)

note right of image #DDFFDD
Declarative Steps:\n
- Fully reproducible\n
- Immutable & deterministic\n
- No configuration drift
end note

note right of dyn_config #DDEEFF
Imperative Steps:\n
- Flexible runtime configuration\n
- Handles dynamic parameters\n
- Minimal and targeted
end note

@enduml
---
