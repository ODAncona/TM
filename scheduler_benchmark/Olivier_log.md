# Log Manuel

J'ai créé ce fichier pour garder une trace de mes actions

2025.03.27 - OK - Réception des identifiants pour le serveur Rhodey
2025.03.28 - OK - Connection à Rhodey en SSH
2025.03.28 - OK - Configuration du SSH agent sur X1-Carbon
2025.03.28 - OK - Ajout de la clé SSH à l'agent
2025.03.28 - OK - Vérification que libvirt est installé sur rhodey
2025.03.28 - OK - Génération d'un fichier opentofu pour Instancier une VM
2025.03.28 - NOK - Test du fichier main.tf : `tofu init` OK `tofu plan` OK `tofu apply` NOK

```txt
╷
│ Error: error while starting the creation of CloudInit's ISO image: exec: "mkisofs": executable file not found in $PATH
│ 
│   with libvirt_cloudinit_disk.cloudinit,
│   on main.tf line 53, in resource "libvirt_cloudinit_disk" "cloudinit":
│   53: resource "libvirt_cloudinit_disk" "cloudinit" {
│ 
╵
```

=> Il semble que `mkisofs` ne soit pas installé sur le serveur Rhodey. Il est nécessaire pour la création de l'image ISO de CloudInit.
2025.03.28 - OK - Installation de `genisoimage` et `mkisofs` sur Rhodey.
2025.03.29 - OK - Investigation du problème `mkisofs`

Your SSH session shows that genisoimage is installed on rhodey (which is functionally equivalent to mkisofs), but the Terraform provider is specifically looking for a command called mkisofs - and it's not finding it in the PATH when executed through the provider.

=> Problème présent sur [GitHub depuis 2022](https://github.com/dmacvicar/terraform-provider-libvirt/issues/934)
=> Conclusion le provider n'est pas à jour sur libvirt et cela engendrera des erreurs. Je considère donc que ce n'est pas une bonne solution pour le moment.
2025.03.29 - OK - Solution de contournement : J'ai découvert qu'il existe un binding sur l'api de `libvirt` en python directement, ce qui me permettra de directement créer une VM sans passer par Terraform. Je compte utiliser cloud-init pour la configuration de la VM.
2025.03.29 - OK - Préparation de package python helper
2025.03.29 - OK - Création d'un helper Python pour `libvirt`
2025.03.29 - OK - Installation de `cdrtools` sur X1-Carbon
2025.03.31 - NOK - Test du fichier main.tf:

```txt
╷
│ Error: error creating libvirt domain: internal error: qemu unexpectedly closed the monitor: 2025-03-31T18:37:31.766303Z qemu-system-x86_64: -blockdev {"driver":"file","filename":"/mnt/vmpool/vms/ubuntu-24.04-server-cloudimg-amd64.img","node-name":"libvirt-3-storage","auto-read-only":true,"discard":"unmap"}: Could not open '/mnt/vmpool/vms/ubuntu-24.04-server-cloudimg-amd64.img': Permission denied
│ 
│   with libvirt_domain.ubuntu_vm,
│   on main.tf line 55, in resource "libvirt_domain" "ubuntu_vm":
│   55: resource "libvirt_domain" "ubuntu_vm" {
│ 
╵
```

2025.03.31 - NOK - Problème de permission sur le fichier image de la VM. Après discussion avec Farzad, il a trouvé qu'il fallait lancer la VM en mode session plutôt que system.

```txt
╷
│ Error: can't retrieve volume /mnt/vmpool/vms/ubuntu_24_04_vm_volume: Storage volume not found: no storage vol with matching key /mnt/vmpool/vms/ubuntu_24_04_vm_volume
│ 
│   with libvirt_domain.ubuntu_vm,
│   on main.tf line 55, in resource "libvirt_domain" "ubuntu_vm":
│   55: resource "libvirt_domain" "ubuntu_vm" {
│ 
╵
```

2025.04.02 - OK - Téléchargement de l'image de la VM sur Rhodey et modification de main.tf

```bash
wget -O /home/odancona/.local/share/libvirt/images/ubuntu-24.04-server-cloudimg-amd64.img https://cloud-images.ubuntu.com/releases/24.04/release/ubuntu-24.04-server-cloudimg-amd64.img
```

2025.04.02 - NOK - Problème d'accès au fichier image de la VM. Impossible même après avoir créé une pool de retrouver l'image de la VM même si elle existe.
2025.04.02 - OK - Création d'un fichier de création de configuration NIX.
2025.04.02 - OK - Création des tests de provisionnement avec libVirt Helper
2025.04.03 - OK - Création des tests pour charger le modèle depuis le fichier de configuration.
2025.04.03 - OK - Configuration de l'image de l'OS. Évaluation entre .iso et qcow2
2025.04.03 - NOK - Nettoyage de volume manuel après échec

```bash
virsh vol-list scheduler_benchmark_pool
virsh vol-delete my-volume scheduler_benchmark_pool
```

2025.04.03 - NOK - Contrôle de l'intégralité de l'image de la VM

```bash
odancona@rhodey:~/.local/share/libvirt/images$ qemu-img check /home/odancona/.local/share/libvirt/images/ubuntu-24.04-server-cloudimg-amd64.img
No errors were found on the image.
28080/57344 = 48.97% allocated, 98.12% fragmented, 97.60% compressed clusters
Image end offset: 611581952
```

```bash
odancona@rhodey:~/.local/share/libvirt/images$ virsh pool-info scheduler_benchmark_pool
Name:           scheduler_benchmark_pool
UUID:           a5b0c71e-c1fc-4e88-8c15-40911aa44b66
State:          running
Persistent:     yes
Autostart:      yes
Capacity:       732.44 GiB
Allocation:     533.97 GiB
Available:      198.48 GiB
```

2025.04.07 - NOK - Création de la VM manuellement avec ISO La VM ne s'installe pas.

```bash
virt-install \
> --name nix-test --memory 4096 --vcpus 4 \
> --cdrom /home/odancona/.local/share/libvirt/images/latest-nixos-minimal-x86_64-linux.iso 
```

Domain is still running. Installation may be in progress.
Waiting for the installation to complete.

2025.04.07 - NOK - Création manuelle de la VM avec l'image qcow2 via l'interface graphique web.

La VM reste bloquée sur netcat ou telnet et impossible de faire la séquence "ctrl + ]"
2025.04.07 - NOK - Test de provision de la VM avec le helper python

Il ne trouve pas l'image car elle doit être ajoutée dans le pool de stockage.

```sh
virsh vol-create-as scheduler_benchmark_pool ubuntu-24.04-server-cloudimg-amd64.img 5G --format qcow2

odancona@rhodey:~$ virsh pool-info scheduler_benchmark_pool
Name:           scheduler_benchmark_pool
UUID:           a5b0c71e-c1fc-4e88-8c15-40911aa44b66
State:          running
Persistent:     yes
Autostart:      yes
Capacity:       732.44 GiB
Allocation:     534.00 GiB
Available:      198.44 GiB

odancona@rhodey:~$ virsh pool-list --all
 Name                       State    Autostart
------------------------------------------------
 boot-scratch               active   yes
 default                    active   yes
 Downloads                  active   yes
 scheduler_benchmark_pool   active   yes
 vms-glusterfs              active   yes

odancona@rhodey:~$ virsh vol-list scheduler_benchmark_pool
 Name                                     Path
-----------------------------------------------------------------------------------------------------------------------------
 latest-nixos-minimal-x86_64-linux.iso    /home/odancona/.local/share/libvirt/images/latest-nixos-minimal-x86_64-linux.iso
 ubuntu-24.04-server-cloudimg-amd64.img   /home/odancona/.local/share/libvirt/images/ubuntu-24.04-server-cloudimg-amd64.img
```

2025.04.07 - NOK - Test de provision de la VM avec le helper python, l'image n'est pas au bon format.

```sh
E           libvirt.libvirtError: internal error: process exited while connecting to monitor: 2025-04-07T22:30:30.816104Z qemu-system-x86_64: -blockdev {"node-name":"libvirt-1-format","read-only":false,"driver":"qcow2","file":"libvirt-1-storage","backing":null}: Image is not in qcow2 format

.venv/lib/python3.13/site-packages/libvirt.py:1379: libvirtError
```

pourtant

```sh
odancona@rhodey:~$ qemu-img info /home/odancona/.local/share/libvirt/images/ubuntu-24.04-server-cloudimg-amd64.img
image: /home/odancona/.local/share/libvirt/images/ubuntu-24.04-server-cloudimg-amd64.img
file format: qcow2
virtual size: 3.5 GiB (3758096384 bytes)
disk size: 583 MiB
cluster_size: 65536
Format specific information:
    compat: 1.1
    compression type: zlib
    lazy refcounts: false
    refcount bits: 16
    corrupt: false
    extended l2: false
```

Le format manquait ! J'ai ajouté

```sh
<target>
    <format type="qcow2"/>
</target>
```

2025.04.08 - OK - Farzad demande pourquoi j'utilie pas `virt-sysprep` et c'est parce que mon wrapper crée les VMs de bout en bout et virt-sysprep est un outil de nettoyage de VM.
2025.04.08 - NOK - Test de provision de la VM avec le helper python, FAILED tests/test_provision.py::test_provision_and_delete_node - assert None is not None probablement à cause d'une mauvaise configuration réseau

```sh
odancona@rhodey:~$ virsh net-dumpxml scheduler_benchmark_net
<network>
  <name>scheduler_benchmark_net</name>
  <uuid>fa5fba2e-fd8e-4fe4-9577-6886503ff618</uuid>
  <forward mode='nat'>
    <nat>
      <port start='1024' end='65535'/>
    </nat>
  </forward>
  <bridge name='virbr2' stp='on' delay='0'/>
  <mac address='52:54:00:e0:76:1b'/>
  <domain name='scheduler_benchmark_net' localOnly='yes'/>
  <dns>
    <host ip='192.168.222.1'>
      <hostname>gateway</hostname>
    </host>
  </dns>
  <ip address='192.168.222.1' netmask='255.255.255.0' localPtr='yes'>
  </ip>
</network>
```

Voici de quoi récupérer la configuration

2025.04.09 - OK - Nettoyage de Nix sur X1-Carbon, nix était mal installé alors j'ai tout nettoyé proprement pour le réinstaller proprement. Pacman a foiré  

```sh
sudo pacman -R nix
sudo rm -rf /nix /etc/nix
sudo groupdel nixbld  # Remove the existing nixbld group
```

2025.04.09 - OK - Réinstallation de Nix sur X1-Carbon Fonctionne !
