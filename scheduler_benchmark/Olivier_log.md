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
2025.04.10 - OK - Apprentissage de Nix et compréhension du Nix SHell
2025.04.11 - OK - Découverte des benchmarks HPC
2025.04.12 - OK - Apprentissage des Nix Flakes
2025.04.13 - OK - Installation de nixos-generators sur X1-Carbon

```
➜  nix git:(main) ✗ nix-env -f https://github.com/nix-community/nixos-generators/archive/master.tar.gz -i
```

2025.04.13 - NOK - Tentative de création d'une image NixOS avec nixos-generators, attributs inexistants

```sh
➜  nix git:(main) ✗ nixos-generate -f qcow -c ./base.nix 
error:
       … while calling the 'seq' builtin
         at /nix/store/zf8yp25bn9lakdca0vad5kp98gij1mkl-nixpkgs/nixpkgs/lib/modules.nix:358:18:
          357|         options = checked options;
          358|         config = checked (removeAttrs config [ "_module" ]);
             |                  ^
          359|         _module = checked (config._module);

       … while calling the 'throw' builtin
         at /nix/store/zf8yp25bn9lakdca0vad5kp98gij1mkl-nixpkgs/nixpkgs/lib/modules.nix:330:13:
          329|           else
          330|             throw baseMsg
             |             ^
          331|         else

       error: The option `description' does not exist. Definition values:
       - In `/home/olivier/projet/tm/scheduler_benchmark/nix/base.nix': "NixOS VM for rhodey"
```

```sh
➜  nix git:(main) ✗ nixos-generate -f qcow -c ./base.nix
error:
       … while calling the 'seq' builtin
         at /nix/store/zf8yp25bn9lakdca0vad5kp98gij1mkl-nixpkgs/nixpkgs/lib/modules.nix:358:18:
          357|         options = checked options;
          358|         config = checked (removeAttrs config [ "_module" ]);
             |                  ^
          359|         _module = checked (config._module);

       … while calling the 'throw' builtin
         at /nix/store/zf8yp25bn9lakdca0vad5kp98gij1mkl-nixpkgs/nixpkgs/lib/modules.nix:330:13:
          329|           else
          330|             throw baseMsg
             |             ^
          331|         else

       error: The option `inputs' does not exist. Definition values:
       - In `/home/olivier/projet/tm/scheduler_benchmark/nix/base.nix':
           {
             nixos-generators = {
               inputs = {
                 nixpkgs = {
                   follows = "nixpkgs";
           ...
```

2025.04.13 - NOK - Séparation du flake en configuration nix standard + run

```sh
➜  nix git:(main) ✗ nixos-generate -f qcow -c ./vm-config.nix 
evaluation warning: system.stateVersion is not set, defaulting to 25.05. Read why this matters on https://nixos.org/manual/nixos/stable/options.html#opt-system.stateVersion.
error:
       … in the condition of the assert statement
         at /nix/store/zf8yp25bn9lakdca0vad5kp98gij1mkl-nixpkgs/nixpkgs/lib/customisation.nix:419:9:
          418|       drvPath =
          419|         assert condition;
             |         ^
          420|         drv.drvPath;

       … while calling the 'seq' builtin
         at /nix/store/zf8yp25bn9lakdca0vad5kp98gij1mkl-nixpkgs/nixpkgs/lib/customisation.nix:105:29:
          104|     in
          105|     flip (extendDerivation (seq drv.drvPath true)) newDrv (
             |                             ^
          106|       {

       … while evaluating the option `system.build.toplevel':

       … while evaluating definitions from `/nix/store/zf8yp25bn9lakdca0vad5kp98gij1mkl-nixpkgs/nixpkgs/nixos/modules/system/activation/top-level.nix':

       … while evaluating the option `virtualisation.diskSize':

       (stack trace truncated; use '--show-trace' to show the full, detailed trace)

       error: The option `virtualisation.diskSize' is defined multiple times while it's expected to be unique.

       Definition values:
       - In `/home/olivier/projet/tm/scheduler_benchmark/nix/vm-config.nix': 16384
       - In `/nix/store/mzhlij6027yakndp60c1kw8h90y0khkw-nixos-generate/share/nixos-generator/nixos-generate.nix': "auto"
       Use `lib.mkForce value` or `lib.mkDefault value` to change the priority on any of these definitions.
```

=> solution utiliser lib.mkForce + fixer le système + ajouter lib en param

2025.04.13 - OK - Première création de l'image QCow2 !

```sh
➜  nix git:(main) ✗ qemu-img info -f qcow2 /nix/store/bc64pli5ij3cvinhid3ax4b888ck00gk-nixos-disk-image/nixos.qcow2
image: /nix/store/bc64pli5ij3cvinhid3ax4b888ck00gk-nixos-disk-image/nixos.qcow2
file format: qcow2
virtual size: 16 GiB (17179869184 bytes)
disk size: 1.52 GiB
cluster_size: 65536
Format specific information:
    compat: 1.1
    compression type: zlib
    lazy refcounts: false
    refcount bits: 16
    corrupt: false
    extended l2: false
Child node '/file':
    filename: /nix/store/bc64pli5ij3cvinhid3ax4b888ck00gk-nixos-disk-image/nixos.qcow2
    protocol type: file
    file length: 1.52 GiB (1628504064 bytes)
    disk size: 1.52 GiB
```

2025.04.13 - NOK - Impossible de lancer l'image avec QEMU elle reste bloquée sur "booting from hard disk"

```sh
sudo qemu-system-x86_64 -hda /nix/store/bc64pli5ij3cvinhid3ax4b888ck00gk-nixos-disk-image/nixos.qcow2 -m 2048 -enable-kvm -net nic -net user,hostfwd=tcp::2222-:22
```

=> downgrade to 24.11

2025.04.13 - NOK - Impossible de lancer l'image avec QEMU elle reste bloquée sur "booting from hard disk"
2025.04.13 - OK - Apprentissage de Nix et connexion avec Sascha Koenig
2025.04.14 - OK - Configuration du fichier `/etc/nix/nix.conf` afin d'ajouter les flakes

```sh
experimental-features = nix-command flakes
```

ça fonctionne

```sh
echo "Hello Nix" | nix run "https://flakehub.com/f/NixOS/nixpkgs/*#ponysay"
```

2025.04.14 - NOK - Tentative 2: Impossible de lancer l'image avec QEMU elle reste bloquée sur "booting from hard disk"

=> il manque une partition de boot !

```sh
➜  nix git:(main) ✗ fdisk -l nixos.img

Disk nixos.img: 1.52 GiB, 1637220352 bytes, 3197696 sectors
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
```

✅ The important part:
nixos-generate -f qcow (or -f qcow2) generates a partition-less raw root filesystem image by default — not a full bootable disk with a partition table and bootloader.

2025.04.14 - OK - je déplace l'image dans le bon répertoire sur rhodey pour tenter de la lancer

```sh
scp nixos.img odancona@rhodey:/home/odancona/.local/share/libvirt/images/nixos.img 
```

2025.04.14 - NOK - Impossible de lancer l'image sur rhodey avec libvirt paraît normal si il n'y a pas de boot !

```sh
 virt-install --name nixos-test --memory 4096 --vcpus 2 --disk path=/home/odancona/.local/share/libvirt/images/nixos.img,format=qcow2 --os-va
riant generic --import --network network=scheduler_benchmark_net -noautoconsole
WARNING  Using --osinfo generic, VM performance may suffer. Specify an accurate OS for optimal results.
WARNING  Graphics requested but DISPLAY is not set. Not running virt-viewer.
WARNING  No console to launch for the guest, defaulting to --wait -1

Starting install...
Creating domain...                                                                                                                                                  |    0 B  00:00:00     

Domain is still running. Installation may be in progress.
Waiting for the installation to complete.
```

=> probably because the image generation fails here's the output log

```sh
Here's the configuration:

{ config, pkgs, lib, ... }: {
    # Boot loader
    boot.kernelPackages = pkgs.linuxPackages_6_1;
    boot.loader.systemd-boot.enable = true;
    boot.loader.efi.canTouchEfiVariables = true;

    # Networking
    networking.hostName = "rhodey-vm";
    networking.interfaces.eth0.useDHCP = true;

    # System Configuration
    time.timeZone = "UTC";
    users.users.odancona = {
        isNormalUser = true;
        initialPassword = "password";
        extraGroups = [ "wheel" ];
        openssh.authorizedKeys.keys = [
            (builtins.readFile /home/olivier/.ssh/rhodey.pub)
            (builtins.readFile /home/olivier/.ssh/id_ed25519.pub)
        ];
    };
    services.openssh.enable = true;
    environment.systemPackages = with pkgs; [
        vim
        curl
        tree
        btop
        bat
        ];
    virtualisation.diskSize = lib.mkForce 16384; # 16GB in MiB
    system.stateVersion = "24.11";
}

Should it be bootable ?

Here's the log of the build:
===
➜  nix git:(main) ✗ nixos-generate -f qcow -c ./vm-config.nix
system-path> created 6802 symlinks in user environment
closure-info> structuredAttrs is enabled
nixos-disk-image> running nixos-install...
nixos-disk-image> copying channel...
...
nixos-disk-image> Warning: The resulting partition is not properly aligned for best performance: 34s % 2048s != 0s
nixos-disk-image> Model:  (file)
nixos-disk-image> Disk /build/nixos.raw: 17.2GB
nixos-disk-image> Sector size (logical/physical): 512B/512B
nixos-disk-image> Partition Table: gpt
nixos-disk-image> Disk Flags:
nixos-disk-image> 
nixos-disk-image> Number  Start   End     Size    File system  Name     Flags
nixos-disk-image>  2      17.4kB  1049kB  1031kB               no-fs    bios_grub
nixos-disk-image>  1      8389kB  269MB   261MB   fat32        ESP      boot, esp
nixos-disk-image>  3      269MB   17.2GB  16.9GB  ext4         primary
nixos-disk-image> 
nixos-disk-image> Warning: The kernel is still using the old partition table.
nixos-disk-image> The new table will be used at the next reboot or after you
nixos-disk-image> run partprobe(8) or kpartx(8)
nixos-disk-image> The operation has completed successfully.
nixos-disk-image> mke2fs 1.47.2 (1-Jan-2025)
nixos-disk-image> Discarding device blocks: done           
nixos-disk-image> Creating filesystem with 4128256 4k blocks and 1032192 inodes
nixos-disk-image> Filesystem UUID: f163c904-0c73-439d-9166-c8d8a3fbe2d5
nixos-disk-image> Superblock backups stored on blocks:
nixos-disk-image>       32768, 98304, 163840, 229376, 294912, 819200, 884736, 1605632, 2654208,
nixos-disk-image>       4096000
nixos-disk-image> 
nixos-disk-image> Allocating group tables: done   
nixos-disk-image> Writing inode tables: done   
nixos-disk-image> Creating journal (16384 blocks): done
nixos-disk-image> Writing superblocks and filesystem accounting information: done   
nixos-disk-image> 
nixos-disk-image> copying staging root to image...
...
nixos-disk-image> WARNING: Image format was not specified for 'nixos.raw' and probing guessed raw.
nixos-disk-image>          Automatically detecting the format is dangerous for raw images, write operations on block 0 will be restricted.
nixos-disk-image>          Specify the 'raw' format explicitly to remove the restrictions.
nixos-disk-image> cSeaBIOS (version rel-1.16.3-0-ga6ed6b701f0a-prebuilt.qemu.org)
nixos-disk-image> 
nixos-disk-image> 
nixos-disk-image> iPXE (http://ipxe.org) 00:03.0 CA00 PCI2.10 PnP PMM+3EFD0C20+3EF30C20 CA00
nixos-disk-image> 
nixos-disk-image> 
nixos-disk-image> 
nixos-disk-image> Booting from ROM...
nixos-disk-image> Probing EDD (edd=off to disable)... oc[    0.332725] sgx: There are zero EPC sections.
nixos-disk-image> loading kernel modules...
nixos-disk-image> mounting Nix store...
nixos-disk-image> mounting host's temporary directory...
nixos-disk-image> starting stage 2 (/nix/store/yac3r4ygkxmkm9c94i8bflakjc2rxm3n-vm-run-stage2)
nixos-disk-image> tune2fs 1.47.2 (1-Jan-2025)
nixos-disk-image> Setting maximal mount count to -1
nixos-disk-image> Setting interval between checks to 0 seconds
nixos-disk-image> Setting time filesystem last checked to Mon Apr 14 19:26:57 2025
nixos-disk-image> 
nixos-disk-image> mkfs.fat 4.2 (2021-01-31)
...
nixos-disk-image> ⚠️ Mount point '/boot' which backs the random seed file is world accessible, which is a security hole! ⚠️
nixos-disk-image> ⚠️ Random seed file '/boot/loader/.#bootctlrandom-seedafd820bfff755b9e' is world accessible, which is a security hole! ⚠️
nixos-disk-image> Random seed file /boot/loader/random-seed successfully written (32 bytes).
nixos-disk-image> Not booted with EFI, skipping EFI variable setup.
nixos-disk-image> Not booted with EFI, skipping EFI variable setup.
nixos-disk-image> tune2fs 1.47.2 (1-Jan-2025)
nixos-disk-image> Setting maximal mount count to -1
nixos-disk-image> Setting interval between checks to 0 seconds
nixos-disk-image> Setting time filesystem last checked to Mon Apr 14 19:26:58 2025
nixos-disk-image> 
nixos-disk-image> tune2fs 1.47.2 (1-Jan-2025)
nixos-disk-image> Setting time filesystem last checked to Thu Jan  1 00:00:00 1970
nixos-disk-image> 
nixos-disk-image> [    3.042460] reboot: Power down
nixos-disk-image> [2025-04-14T19:26:58Z INFO  virtiofsd] Client disconnected, shutting down
nixos-disk-image> [2025-04-14T19:26:58Z INFO  virtiofsd] Client disconnected, shutting down
/nix/store/qin6miwj5ch0mcl2yh8f8gb6zsgxjyr1-nixos-disk-image/nixos.qcow2
```

2025.04.14 - OK - Recréation de la VM mais avec le bon bootloader

```sh
odancona@rhodey:~/.local/share/libvirt/images$ virt-install   --name nixos-test   --memory 4096 --vcpus 2   --disk path=/home/odancona/.local/share/libvirt/images/nixos.img,format=qcow2   --os-variant generic   --import   --network network=scheduler_benchmark_net   --boot loader=/usr/share/OVMF/OVMF_CODE.fd   --noautoconsole
chmod 777 nixos.img
```

2025.04.14 - OK - La VM Démarre MILESTONE 2

```sh
virsh start nixos-test --console
```

2025.04.14 - NOK - La VM ne se connecte pas au réseau

Déboggage résea

```sh
[odancona@rhodey-vm:~]$ ls /sys/class/net
eth0  lo

[odancona@rhodey-vm:~]$ ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host noprefixroute 
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 52:54:00:0c:e0:b0 brd ff:ff:ff:ff:ff:ff
    inet 169.254.238.143/16 brd 169.254.255.255 scope global noprefixroute eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::5054:ff:fe0c:e0b0/64 scope link 
       valid_lft forever preferred_lft forever

[odancona@rhodey-vm:~]$ ping 8.8.8.8
PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.

--- 8.8.8.8 ping statistics ---
3 packets transmitted, 0 received, 100% packet loss, time 2080ms

odancona@rhodey:~$ virsh net-dumpxml scheduler_benchmark_net
<network connections='1'>
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

odancona@rhodey:~/.local/share/libvirt/images$ virsh net-list --all
 Name                      State    Autostart   Persistent
------------------------------------------------------------
 bxenet                    active   yes         yes
 default                   active   yes         yes
 p38                       active   yes         yes
 scheduler_benchmark_net   active   yes         yes

[odancona@rhodey-vm:~]$ sudo systemctl restart systemd-networkd

We trust you have received the usual lecture from the local System
Administrator. It usually boils down to these three things:

    #1) Respect the privacy of others.
    #2) Think before you type.
    #3) With great power comes great responsibility.

For security reasons, the password you type will not be visible.

[sudo] password for odancona: 
Failed to restart systemd-networkd.service: Unit systemd-networkd.service not found.

[odancona@rhodey-vm:~]$ sudo dhclient eth0
sudo: dhclient: command not found
```
