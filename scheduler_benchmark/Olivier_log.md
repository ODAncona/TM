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
2025.04.02 - OK - Création des tests de provisionnement avec libVirt Helper. Le Wrapper fonctionne correctement mais ne permet pas encore de provisionner une VM à partir d'une image qcow2.
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

2025.04.04 - OK - Amélioration de la configuration du helper pour la rendre générique

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

2025.04.09 - OK - Première provision de la VM avec le helper python 🎉 MILESTONE 1 🎉

2025.04.10 - OK - Nettoyage de Nix sur X1-Carbon, nix était mal installé alors j'ai tout nettoyé proprement pour le réinstaller proprement. Pacman a foiré

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

2025.04.14 - OK - La VM Démarre 🎉 MILESTONE 2 🎉

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

2025.04.14 - NOK - La VM ne se connecte pas au réseau

C'est dhcp et l'interface qu'il faut bien configurer.

Rapport d'analyse:

```sh
[odancona@rhodey-vm:~]$  systemctl status systemd-networkd
● systemd-networkd.service - Network Configuration
     Loaded: loaded (/etc/systemd/system/systemd-networkd.service; enabled; preset: ignored)
    Drop-In: /nix/store/kh1v7yn1jz76n2gljmlyf94c4kvcic9g-system-units/systemd-networkd.service.d
             └─overrides.conf
     Active: active (running) since Mon 2025-04-14 21:50:03 UTC; 2min 53s ago
 Invocation: 3dd79932715a44d8ad3d1fb3c716953a
TriggeredBy: ● systemd-networkd.socket
       Docs: man:systemd-networkd.service(8)
             man:org.freedesktop.network1(5)
   Main PID: 587 (systemd-network)
     Status: "Processing requests..."
         IP: 0B in, 336B out
         IO: 2M read, 0B written
      Tasks: 1 (limit: 4682)
   FD Store: 0 (limit: 512)
     Memory: 3.7M (peak: 3.9M)
        CPU: 65ms
     CGroup: /system.slice/systemd-networkd.service
             └─587 /nix/store/b2cfj7yk3wfg1jdwjzim7306hvsc5gnl-systemd-257.3/lib/systemd/systemd-networkd

Apr 14 21:50:03 rhodey-vm systemd[1]: Starting Network Configuration...
Apr 14 21:50:03 rhodey-vm systemd-networkd[587]: lo: Link UP
Apr 14 21:50:03 rhodey-vm systemd-networkd[587]: lo: Gained carrier
Apr 14 21:50:03 rhodey-vm systemd[1]: Started Network Configuration.
Apr 14 21:50:04 rhodey-vm systemd-networkd[587]: eth0: Interface name change detected, renamed to ens3.
Apr 14 21:50:04 rhodey-vm systemd-networkd[587]: ens3: Configuring with /etc/systemd/network/10-ethernet-dhcp.network.
Apr 14 21:50:04 rhodey-vm systemd-networkd[587]: ens3: Link UP
Apr 14 21:50:06 rhodey-vm systemd-networkd[587]: ens3: Gained carrier
Apr 14 21:50:07 rhodey-vm systemd-networkd[587]: ens3: Gained IPv6LL

[odancona@rhodey-vm:~]$ bat /etc/systemd/network/10-ethernet-dhcp.network
───────┬───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
       │ File: /etc/systemd/network/10-ethernet-dhcp.network
───────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1   │ [Match]
   2   │ Name=en*
   3   │
   4   │ [Network]
   5   │ DHCP=yes
   6   │
───────┴───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

[odancona@rhodey-vm:~]$ ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host noprefixroute
       valid_lft forever preferred_lft forever
2: ens3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 52:54:00:77:8c:05 brd ff:ff:ff:ff:ff:ff
    altname enp0s3
    altname enx525400778c05
    inet6 fe80::5054:ff:fe77:8c05/64 scope link proto kernel_ll
       valid_lft forever preferred_lft forever

[odancona@rhodey-vm:~]$ ping 8.8.8.8
ping: connect: Network is unreachable
```

Il y a un problème d'interface selon la configuration. Je test avec une config simplifiée:

```sh
    # Networking
    networking.hostName = "nix-vm";
    networking.useDHCP = true;
    networking.useNetworkd = true;
    systemd.network.enable = true;
```

Il fallait simplement changer le DHCP il manquait la balise <dhcp></dhcp>

```sh
<network>
  <name>scheduler_benchmark_net</name>
  <uuid>fa5fba2e-fd8e-4fe4-9577-6886503ff618</uuid>
  <forward mode='nat'/>
  <bridge name='virbr2' stp='on' delay='0'/>
  <mac address='52:54:00:e0:76:1b'/>
  <domain name='scheduler_benchmark_net' localOnly='yes'/>
  <dns>
    <host ip='192.168.222.1'>
      <hostname>gateway</hostname>
    </host>
  </dns>
  <ip address='192.168.222.1' netmask='255.255.255.0' localPtr='yes'>
    <dhcp>
      <range start='192.168.222.100' end='192.168.222.254'/>
    </dhcp>
  </ip>
</network>
```

2025.04.14 - OK - La VM se connecte à internet 🎉 MILESTONE 3 🎉
2025.04.15 - OK - Préparation de la présentation de meeting 5
2025.04.15 - Ok - Préparation de la configuration de NixOS Installation
2025.04.15 - OK - Réparation des tests de libvirt
2025.04.15 - OK - Meeting avec Philippe Walther
2025.04.16 - OK - Meeting 4 avec George et Sébastien
2025.04.16 - OK - Meeting avec Sascha Koenig pour discuter de la création d'une image NixOS
2025.04.16 - OK - Rédaction Email pour Tamar
2025.04.17 - OK - Exploration de comment configurer Kubernetes
2025.04.17 - OK - Visionnage de la conférence Josh Rosso a devkon sur Kubernetes cluster on Nix
2025.04.17 - NOK - Configuration du flake

```sh
➜  nix git:(main) ✗ nix build .#nix-vm-image

warning: Git tree '/home/olivier/projet/tm' is dirty
error:
       … while evaluating the attribute 'config.system.build."${(image).config.formatAttr}"'
         at /nix/store/hzaj4d6ari2wq2cbg1j60n9zw42gnshy-source/lib/modules.nix:359:9:
          358|         options = checked options;
          359|         config = checked (removeAttrs config [ "_module" ]);
             |         ^
          360|         _module = checked (config._module);

       … while calling the 'seq' builtin
         at /nix/store/hzaj4d6ari2wq2cbg1j60n9zw42gnshy-source/lib/modules.nix:359:18:
          358|         options = checked options;
          359|         config = checked (removeAttrs config [ "_module" ]);
             |                  ^
          360|         _module = checked (config._module);

       (stack trace truncated; use '--show-trace' to show the full, detailed trace)

       error: attribute 'qcow2' missing
```

=> Je n'arrive pas à utiliser nix-generators dans le flake afin d'étendre la config avec un module configurable
2025.04.18 - OK - Réunion avec Tamar Vered pour discuter du visa J-1 => impossible d'avoir un travail sur le côté
2025.04.18 - OK - Apprentissage de nix-language
2025.04.18 - OK - Mise à jour de la spécification
2025.04.18 - OK - Exploration de NixOS + Kubernetes
2025.04.18 - OK - Transformation de la vm-config en module
2025.04.18 - NOK - Impossible de créer l'image du k8s master avec nixos-generators

```sh
error: builder for '/nix/store/m57qxz49snzg9pz8x8jm60ddab1b3lns-etcdserver-3.5.16.drv' failed with exit code 1;
       last 25 log lines:
       > {"level":"warn","ts":"2025-04-19T03:12:29.089505Z","caller":"embed/config.go:689","msg":"Running http and grpc server on single port. This is not recommended for production."}
       > {"level":"warn","ts":"2025-04-19T03:12:29.089791Z","caller":"embed/config.go:689","msg":"Running http and grpc server on single port. This is not recommended for production."}
       > {"level":"warn","ts":"2025-04-19T03:12:29.089817Z","caller":"embed/config.go:689","msg":"Running http and grpc server on single port. This is not recommended for production."}
       > {"level":"warn","ts":"2025-04-19T03:12:29.090042Z","caller":"embed/config.go:689","msg":"Running http and grpc server on single port. This is not recommended for production."}
       > {"level":"warn","ts":"2025-04-19T03:12:29.090537Z","caller":"embed/config.go:689","msg":"Running http and grpc server on single port. This is not recommended for production."}
       > {"level":"warn","ts":"2025-04-19T03:12:29.090640Z","caller":"embed/config.go:689","msg":"Running http and grpc server on single port. This is not recommended for production."}
       > {"level":"warn","ts":"2025-04-19T03:12:29.090726Z","caller":"embed/config.go:689","msg":"Running http and grpc server on single port. This is not recommended for production."}
       > {"level":"warn","ts":"2025-04-19T03:12:29.091044Z","caller":"embed/config.go:689","msg":"Running http and grpc server on single port. This is not recommended for production."}
       > {"level":"info","ts":"2025-04-19T03:12:29.091055Z","caller":"embed/etcd.go:128","msg":"configuring peer listeners","listen-peer-urls":["unix://localhost:15405000001"]}
       > {"level":"info","ts":"2025-04-19T03:12:29.091121Z","caller":"embed/etcd.go:136","msg":"configuring client listeners","listen-client-urls":["unix://localhost:15405000000"]}
       > {"level":"info","ts":"2025-04-19T03:12:29.091205Z","caller":"embed/etcd.go:311","msg":"starting an etcd server","etcd-version":"3.5.16","git-sha":"GitNotFound","go-version":"go1.24.1","go-os":"linux","go-arch":"amd64","max-cpu-set":8,"max-cpu-available":8,"member-initialized":false,"name":"default","data-dir":"/build/TestStartEtcdWrongToken609188304/001/token-test3242343331","wal-dir":"","wal-dir-dedicated":"","member-dir":"/build/TestStartEtcdWrongToken609188304/001/token-test3242343331/member","force-new-cluster":false,"heartbeat-interval":"100ms","election-timeout":"1s","initial-election-tick-advance":true,"snapshot-count":100000,"max-wals":5,"max-snapshots":5,"snapshot-catchup-entries":5000,"initial-advertise-peer-urls":["unix://localhost:15405000001"],"listen-peer-urls":["unix://localhost:15405000001"],"advertise-client-urls":["unix://localhost:15405000000"],"listen-client-urls":["unix://localhost:15405000000"],"listen-metrics-urls":[],"cors":["*"],"host-whitelist":["*"],"initial-cluster":"default=unix://localhost:15405000001","initial-cluster-state":"new","initial-cluster-token":"etcd-cluster","quota-backend-bytes":2147483648,"max-request-bytes":1572864,"max-concurrent-streams":4294967295,"pre-vote":true,"initial-corrupt-check":false,"corrupt-check-time-interval":"0s","compact-check-time-enabled":false,"compact-check-time-interval":"1m0s","auto-compaction-mode":"","auto-compaction-retention":"0s","auto-compaction-interval":"0s","discovery-url":"","discovery-proxy":"","downgrade-check-interval":"5s"}
       > {"level":"info","ts":"2025-04-19T03:12:29.091429Z","caller":"etcdserver/backend.go:81","msg":"opened backend db","path":"/build/TestStartEtcdWrongToken609188304/001/token-test3242343331/member/snap/db","took":"82.825µs"}
       > {"level":"info","ts":"2025-04-19T03:12:29.103883Z","caller":"etcdserver/raft.go:505","msg":"starting local member","local-member-id":"be92390084cabfc6","cluster-id":"80a83306c08a3ac6"}
       > {"level":"info","ts":"2025-04-19T03:12:29.103939Z","logger":"raft","caller":"etcdserver/zap_raft.go:77","msg":"be92390084cabfc6 switched to configuration voters=()"}
       > {"level":"info","ts":"2025-04-19T03:12:29.103973Z","logger":"raft","caller":"etcdserver/zap_raft.go:77","msg":"be92390084cabfc6 became follower at term 0"}
       > {"level":"info","ts":"2025-04-19T03:12:29.103997Z","logger":"raft","caller":"etcdserver/zap_raft.go:77","msg":"newRaft be92390084cabfc6 [peers: [], term: 0, commit: 0, applied: 0, lastindex: 0, lastterm: 0]"}
       > {"level":"info","ts":"2025-04-19T03:12:29.104003Z","logger":"raft","caller":"etcdserver/zap_raft.go:77","msg":"be92390084cabfc6 became follower at term 1"}
       > {"level":"info","ts":"2025-04-19T03:12:29.104023Z","logger":"raft","caller":"etcdserver/zap_raft.go:77","msg":"be92390084cabfc6 switched to configuration voters=(13732100888196726726)"}
       > {"level":"warn","ts":"2025-04-19T03:12:29.104150Z","caller":"auth/store.go:1253","msg":"unknown token type","type":"wrong-token","error":"auth: invalid auth options"}
       > {"level":"warn","ts":"2025-04-19T03:12:29.104169Z","caller":"etcdserver/server.go:615","msg":"failed to create token provider","error":"auth: invalid auth options"}
       > {"level":"info","ts":"2025-04-19T03:12:29.104250Z","caller":"embed/etcd.go:378","msg":"closing etcd server","name":"default","data-dir":"/build/TestStartEtcdWrongToken609188304/001/token-test3242343331","advertise-peer-urls":["unix://localhost:15405000001"],"advertise-client-urls":["unix://localhost:15405000000"]}
       > {"level":"info","ts":"2025-04-19T03:12:29.104293Z","caller":"embed/etcd.go:380","msg":"closed etcd server","name":"default","data-dir":"/build/TestStartEtcdWrongToken609188304/001/token-test3242343331","advertise-peer-urls":["unix://localhost:15405000001"],"advertise-client-urls":["unix://localhost:15405000000"]}
       > FAIL
       > FAIL     go.etcd.io/etcd/server/v3/embed 0.471s
       > FAIL
       For full logs, run:
         nix log /nix/store/m57qxz49snzg9pz8x8jm60ddab1b3lns-etcdserver-3.5.16.drv
error: 1 dependencies of derivation '/nix/store/i1rjksysqsl090a5p0hdv724vsa98i4m-etcd-3.5.16.drv' failed to build
error: 1 dependencies of derivation '/nix/store/qkcx52yz68kvawmq54ll0yh36wimcm6m-system-path.drv' failed to build
error: 1 dependencies of derivation '/nix/store/pnqafjhs6kywrmxfrqq6ngvqm02kik9q-unit-etcd.service.drv' failed to build
error: 1 dependencies of derivation '/nix/store/67a48d0ghgzr02fxbwfdii6a5kxfym90-nixos-system-nix-vm-25.05pre780817.b2b0718004cc.drv' failed to build
error: 1 dependencies of derivation '/nix/store/fd2wcnc4l1mqyl8wzca7m6gbwpzyl9ql-nixos-disk-image.drv' failed to build
```

2025.04.19 - OK - Learn NixModule, nix-tour, flakes
2025.04.19 - OK - Analyse de la configuration des IPs K8s static vs dhcp
2025.04.20 - NOK - Impossible de générer l'image

```sh
       error: undefined variable 'masterIP'
       at /home/olivier/projet/tm/scheduler_benchmark/nix/vm-config.nix:45:16:
           44|     inherit config lib pkgs;
           45|     masterIP = masterIP;
             |                ^
           46|   };
```

Je dois définir l'ip manuellement ce qui pose problème pour DHCP
=> Fix manuel ip

```sh
FAIL    go.etcd.io/etcd/server/v3/embed 1.020s
```

=> j'essaie de voir si etcd compile normalement et j'observe la même erreur.

```sh
nix build nixpkgs#etcd
...
       > FAIL
       > FAIL  go.etcd.io/etcd/server/v3/embed 0.770s
       > FAIL
       For full logs, run:
         nix log /nix/store/2c03p6zg8j8jbb4926pabpdlrrvrkhpq-etcdserver-3.5.16.drv
error: 1 dependencies of derivation '/nix/store/1mj2l2xc76a70rrlbwwc020rbsy7h3mw-etcd-3.5.16.drv' failed to build
```

=> trouvé le problème sur git <https://github.com/NixOS/nixpkgs/issues/390588> et sera résolu dans la prochaine version de nixpkgs. Donc je vais rétrograder à la version stable de nixOs.

```sh
nix-channel --add https://nixos.org/channels/nixos-23.11 nixos
nix-channel --update
```

=> échec car la version 23.11 n'a pas la même api erreur de disk-size-option

2025.04.21 - OK - Analyse du runtime. Comme j'ai besoin de l'IP pour configurer le master avec kubernetes pour Nix. J'ai un problème de runtime. Je dois donc séparer la préparation de l'image et le runtime. (impératif vs déclaratif)
2025.04.21 - NOK - Impossible de générer l'image

```sh
error:
       … while evaluating the attribute 'config.system.build."${(image).config.formatAttr}"'
         at /nix/store/g8zzlf6drg73c987ii390yicq4c0j778-source/lib/modules.nix:320:9:
          319|         options = checked options;
          320|         config = checked (removeAttrs config [ "_module" ]);
             |         ^
          321|         _module = checked (config._module);

       … while calling the 'seq' builtin
         at /nix/store/g8zzlf6drg73c987ii390yicq4c0j778-source/lib/modules.nix:320:18:
          319|         options = checked options;
          320|         config = checked (removeAttrs config [ "_module" ]);
             |                  ^
          321|         _module = checked (config._module);

       (stack trace truncated; use '--show-trace' to show the full, detailed trace)

       error: path '/nix/store/g8zzlf6drg73c987ii390yicq4c0j778-source/nixos/modules/virtualisation/disk-size-option.nix' does not exist
```

=> Fonctionne avec nixos-generate -f qcow -c ./vm-config.nix mais pas avec le flake

Solution mettre à jour le nixpkgs à 24.11

2025.04.21 - NOK - Impossible de générer l'image

```sh
error: access to absolute path '/home' is forbidden in pure evaluation mode (use '--impure' to override)
```

=>  nix build .#qcow --impure
2025.04.21 - NOK - Image générée avec le flake
2025.04.21 - NOK - Impossible de démarrer la VM

```sh
ERROR    internal error: qemu unexpectedly closed the monitor: 2025-04-22T01:02:22.270461Z qemu-system-x86_64: -blockdev {"node-name":"libvirt-1-format","read-only":false,"driver":"qcow2","file":"libvirt-1-storage","backing":null}: qcow2: Image is corrupt; cannot be opened read/write
Domain installation does not appear to have been successful.
If it was, you can restart your domain by running:
  virsh --connect qemu:///system start nixos-test2
otherwise, please restart your installation.
```

=> regénérer l'image avec qcow2 et retéléverser et fonctionne !

2025.04.21 - OK - Génération de l'image avec le Kubernetes master
2025.04.21 - NOK - Démarrage de la VM avec le master k8s

=> ERROR etcd not started

2025.04.22 - OK - Analyse sur la réorganisation de la stack + infographie
2025.04.22 - OK - Modification de la configuration du worker nix + password hashed
2025.04.22 - OK - Build de l'image `nixos-k8s-master` et `nixos-k8s-worker` + upload sur rhodey
2025.04.22 - OK - Mise à jour de la configuration du réseau
2025.04.22 - NOK - Impossible de démarrer la VM avec le master k8s

```sh
[2025-04-22 15:08:48,488][scheduler_benchmark.vm.libvirt_helper][INFO] - Création du volume 'head-node-1_disk' de 16GB basé sur 'nixos-k8s-master'
libvirt: Storage Driver error : Storage volume not found: no storage vol with matching name 'nixos-k8s-master'
[2025-04-22 15:08:48,528][scheduler_benchmark.vm.libvirt_helper][WARNING] - Base image 'nixos-k8s-master' non trouvée dans le pool: Storage volume not found: no storage vol with matching name 'nixos-k8s-master'
[2025-04-22 15:08:48,528][scheduler_benchmark.vm.libvirt_helper][ERROR] - Base image 'nixos-k8s-master' not found in storage pool 'scheduler_benchmark_pool'. Please add it to the pool first using standard libvirt tools.
[2025-04-22 15:08:48,529][scheduler_benchmark.vm.libvirt_helper][INFO] - Déconnexion de l'hôte libvirt rhodey.lbl.gov
[2025-04-22 15:08:48,529][__main__][ERROR] - Error provisioning node: Base image 'nixos-k8s-master' not found in storage pool 'scheduler_benchmark_pool'. Please add it to the pool first using standard libvirt tools.
```

=> `image: "nixos-k8s-master` => `image: "nixos-k8s-master.img"`
=> OK !
2025.04.22 - NOK - Impossible de récupérer l'IP du noeud.
=> [2025-04-22 15:13:27,810][__main__][ERROR] - Error provisioning node: VM head-node-1 did not obtain an IP
=> Impossible de se connecter à la VM même avec la console.
=>

```sh
odancona@rhodey:~$ virsh list --all
 Id   Name          State
------------------------------
 1    firesim-03    running
 6    ubuntu22.04   running
 41   head-node-1   running
 -    p38vm         shut off
 -    p38vm-25      shut off
 -    p38vm-45      shut off
 ```

Création d'une VM avec l'image du master

```
odancona@rhodey:~$ virt-install   --name nixos-test-k8s   --memory 4096 --vcpus 2   --disk path=/home/odancona/.local/share/libvirt/images/nixos-k8s-master.img,format=qcow2   --os-variant generic   --import   --network network=scheduler_ben
chmark_net   --boot loader=/usr/share/OVMF/OVMF_CODE.fd   --noautoconsole
WARNING  Using --osinfo generic, VM performance may suffer. Specify an accurate OS for optimal results.
```

=> Preuve que l'image fonctionne bien
=> Problème identifié, le bootloader n'était pas spécifié dans le XML
=>

```xml
<os>
  <type arch='x86_64' machine='q35'>hvm</type>
  <loader readonly='yes' type='pflash'>/usr/share/OVMF/OVMF_CODE.fd</loader>
  <boot dev='hd'/>
</os>
```

=> [2025-04-23 13:29:13,977][__main__][ERROR] - Error provisioning node: unsupported configuration: UEFI requires ACPI on this architecture
=> L'expérience explose car le volume existe déjà. Alors je le supprime

```txt
[2025-04-23 13:33:36,822][scheduler_benchmark.vm.libvirt_helper][INFO] - Création du volume 'head-node-1_disk' de 16GB basé sur 'nixos-k8s-master.img'
libvirt: Storage Driver error : internal error: storage volume name 'head-node-1_disk' already in use.
[2025-04-23 13:33:36,831][scheduler_benchmark.vm.libvirt_helper][WARNING] - Base image 'nixos-k8s-master.img' non trouvée dans le pool: internal error: storage volume name 'head-node-1_disk' already in use.
[2025-04-23 13:33:36,832][scheduler_benchmark.vm.libvirt_helper][ERROR] - Base image 'nixos-k8s-master.img' not found in storage pool 'scheduler_benchmark_pool'. Please add it to the pool first using standard libvirt tools.
[2025-04-23 13:33:36,833][scheduler_benchmark.vm.libvirt_helper][INFO] - Déconnexion de l'hôte libvirt rhodey.lbl.gov
[2025-04-23 13:33:36,834][__main__][ERROR] - Error provisioning node: Base image 'nixos-k8s-master.img' not found in storage pool 'scheduler_benchmark_pool'. Please add it to the pool first using standard libvirt tools.
```

=> SUCCESS [2025-04-23 13:35:36,255][__main__][INFO] - Node head-node-1 provisioned with IP: 192.168.222.182

2025.04.23 - NOK - Impossible de lancer le k8s-worker

```sh
[2025-04-23 13:35:36,256][__main__][ERROR] - Error provisioning node: 'ClusterConfig' object has no attribute 'worker_nodes'
```

=> "worker_node" => "compute_node"
=> OK
2025.04.23 - OK - Analyse de la configuration de l'IP:

ip fixe => facile mais pas flexible pour créer image
ip dhcp => flexible mais moins facile à gérer
2025.04.23 - OK - Analyse de la méthode d'initialisation de la runtime configuration
2025.04.23 - OK - Refactor de la codebase, simplification de l'API (assigner baseimage au node)
2025.04.23 - OK - Génération de k8s cluster gen
2025.04.23 - NOK - Génération de l'image du master avec la config modifiée de k8s

```sh
   error: The option `services.kubernetes.masterAddress' was accessed but has no value defined. Try setting the option.
```

=> masterAddress doit être connu à la construction de la configuration Nix, alors que dans beaucoup de scénarios (cloud, VM dynamiques), on ne connaît l’IP du master qu’au runtime.
=> analyser le module nix
=> Conclusion, il faut enlever la configuration statique

```sh
There are generally two ways of enabling Kubernetes on NixOS. One way is to enable and configure cluster components appropriately by hand:

services.kubernetes = {
  apiserver.enable = true;
  controllerManager.enable = true;
  scheduler.enable = true;
  addonManager.enable = true;
  proxy.enable = true;
  flannel.enable = true;
};
Another way is to assign cluster roles (“master” and/or “node”) to the host. This enables apiserver, controllerManager, scheduler, addonManager, kube-proxy and etcd:
```

=> même erreur
=> C’est easyCerts = true qui force la dépendance à masterAddress, même si tu n’utilises pas roles.
=> Même sans roles et sans easyCerts, le module attend toujours que services.kubernetes.masterAddress soit défini dès qu'on active certains sous-modules (par ex. l'apiserver, le controllerManager, le scheduler ou le kubelet).
=> Le hack rapide : définir masterAddress à une valeur bidon
2025.04.24 - NOK - Impossible de compiler l'image
L'ordinateur freeze complètement
=> solution hard reboot et nettoyage du nix store avec le garbage collector
=> `nix-collect-garbage -d`
2025.04.25 - NOK - Impossible de configurer Kubernetes
=>

```sh
[odancona@nixos:~]$ kubectl get all
E0426 03:36:22.611118    5166 memcache.go:265] "Unhandled Error" err="couldn't get current server API group list: Get \"http://localhost:8080/api?timeout=32s\": dial tcp [::1]:8080: connect: connection refused"
```

=> Je dois modifier la configuration pour utiliser une IP fixe
=> Je tente de placer une ip fixe au master
=> il ne peut pas configurer car l'interface `enp1s0` n'existe plus alors qu'elle est présente en dhcp.
=> Dans ta config Nix, remplace partout enp1s0 par ens3 :

2025.04.27 - NOK - Test de la configuration de l'IP
Lorsque je configure enp1s0, j'ai une ip sur ens3 et lorsque je configure ens3 j'ai une ip sur enp1s0.
=> Abandon de l'idée de configurer Kubernetes avec Nix
=> Test d'une approche manuelle

2025.04.28 - OK - Analyse Ansible vs python
2025.04.29 - OK - Création du Rapport et réglage de police et compilation
2025.04.29 - OK - Création d'une image avec les paquets de base
2025.04.29 - NOK - Impossible de kubeadm init

```sh
[odancona@nixos:~]$ sudo kubeadm init
I0429 19:53:06.467547    4138 version.go:261] remote version is much newer: v1.33.0; falling back to: stable-1.31
[init] Using Kubernetes version: v1.31.8
[preflight] Running pre-flight checks
W0429 19:53:06.716363    4138 checks.go:1080] [preflight] WARNING: Couldn't create the interface used for talking to the container runtime: failed to create new CRI runtime service: validate service connection: validate CRI v1 runtime API for endpoint "unix:///var/run/containerd/containerd.sock": rpc error: code = Unavailable desc = connection error: desc = "transport: Error while dialing: dial unix /var/run/containerd/containerd.sock: connect: no such file or directory"
        [WARNING FileExisting-crictl]: crictl not found in system path
        [WARNING Service-Kubelet]: kubelet service is not enabled, please run 'systemctl enable kubelet.service'
error execution phase preflight: [preflight] Some fatal errors occurred:
        [ERROR FileExisting-conntrack]: conntrack not found in system path
        [ERROR FileContent--proc-sys-net-ipv4-ip_forward]: /proc/sys/net/ipv4/ip_forward contents are not set to 1
[preflight] If you know what you are doing, you can make a check non-fatal with `--ignore-preflight-errors=...`
To see the stack trace of this error execute with --v=5 or higher
```

=> ajout de conntrack-tools avec `nix profile install nixpkgs#conntrack-tools`
=> Activation de containerd `virtualisation.containerd.enable = true;`

```sh
I0429 21:08:06.626789    3261 version.go:261] remote version is much newer: v1.33.0; falling back to: stable-1.31
[init] Using Kubernetes version: v1.31.8
[preflight] Running pre-flight checks
W0429 21:08:06.834913    3261 checks.go:1080] [preflight] WARNING: Couldn't create the interface used for talking to the container runtime: failed to create new CRI runtime service: validate service connection: validate CRI v1 runtime API for endpoint "unix:///var/run/containerd/containerd.sock": rpc error: code = Unavailable desc = connection error: desc = "transport: Error while dialing: dial unix /var/run/containerd/containerd.sock: connect: no such file or directory"
        [WARNING Service-Kubelet]: kubelet service is not enabled, please run 'systemctl enable kubelet.service'
error execution phase preflight: [preflight] Some fatal errors occurred:
        [ERROR FileContent--proc-sys-net-ipv4-ip_forward]: /proc/sys/net/ipv4/ip_forward contents are not set to 1
[preflight] If you know what you are doing, you can make a check non-fatal with `--ignore-preflight-errors=...`
To see the stack trace of this error execute with --v=5 or higher
```

=> Ajout de ces changements

```nix
  boot.kernel.sysctl = {
    "net.ipv4.ip_forward" = 1;
    "net.bridge.bridge-nf-call-iptables" = 1;
    "net.bridge.bridge-nf-call-ip6tables" = 1;
  };
  virtualisation.containerd = {
    enable = true;
    settings = {
      plugins."io.containerd.grpc.v1.cri".enable = true;
    };
  };
```

=> Impossible de démarrer le kubelet à cause de la même erreur de configuration de l'IP
=> Je vais réessayer de configurer l'IP
2025.04.30 - OK - Extension du flake pour plus d'évolutivité on peut appeler le flakes comme ça `nix build .#k8s-master --impure`
2025.04.30 - OK - Compilation du master et du worker avec un hostName du master défini à `nixos-k8s-master`
2025.04.30 - NOK - Impossible de résoudre l'IP du master

=> Il manque le DHCP
=>
`virsh net-edit scheduler_benchmark_net`

```xml
  <dns enable='yes'>
    <host ip='192.168.222.1'>
      <hostname>gateway</hostname>
    </host>
  </dns>
```

=>

```sh
virsh net-destroy scheduler_benchmark_net
virsh net-start scheduler_benchmark_net
```

2025.04.30 - NOK - Echec de connection via hostname worker -> master!

=> Il faut configurer soit Avahi/mDNS soit DNS dynamique avec libvirt

```nix
services.avahi = {
  enable = true;
  nssmdns4 = true;  # Intégration avec la résolution de noms du système
  publish = {
    enable = true;
    addresses = true;
    domain = true;
    workstation = true;
  };
};
```

+ `nixos-k8s-master.local`

=> Success

```sh
[odancona@nixos:~]$ ping nixos-k8s-master.local
PING nixos-k8s-master.local (192.168.222.107) 56(84) bytes of data.
64 bytes from nixos-k8s-master.scheduler_benchmark_net (192.168.222.107): icmp_seq=1 ttl=64 time=0.508 ms
64 bytes from nixos-k8s-master.scheduler_benchmark_net (192.168.222.107): icmp_seq=2 ttl=64 time=0.418 ms
64 bytes from nixos-k8s-master.scheduler_benchmark_net (192.168.222.107): icmp_seq=3 ttl=64 time=0.469 ms
```

2025.04.30 - NOK - Impossible de récupérer les noeuds du cluster

=> Il faut sur le master

```sh
export KUBECONFIG=/etc/kubernetes/cluster-admin.kubeconfig
sudo kubectl
```

=> succès mais ça ne fonctionnera pas sur le worker

```sh
[odancona@nixos-k8s-master:~]$ sudo kubectl --kubeconfig=/etc/kubernetes/cluster-admin.kubeconfig get nodes
NAME               STATUS   ROLES    AGE   VERSION
nixos-k8s-master   Ready    <none>   15m   v1.31.2
```

=> Test de configuration permanente en ajoutant `services.kubernetes.masterAddress = "nixos-k8s-master.local";`
=> Même erreur
=> Au moment du build des certificats (easyCerts), le système ne peut pas faire de résolution mDNS → il a besoin d’un nom résolu localement.
=> Il faut donc configurer le DNS proprement sur le master et le worker car easyCerts doit générer un certificat avec le bon CN (Common Name) ou SAN (Subject Alt Name). En utilisant: apiserverAddress = "<https://nixos-k8s-master.local:6443>", le système ne peut pas résoudre ce nom au moment du build. Donc Le certificat ne contient pas cette adresse et les workers recevront un certificat TLS pour un autre nom → erreur de validation TLS.
=> J'ai essayé de déterminer le même hostname sur les deux machines mais le nom ne passe pas
=>

```sh
error: A definition for option `networking.hostName' is not of type `string matching the pattern ^$|^[[:alnum:]]([[:alnum:]_-]{0,61}[[:alnum:]])?$'. Definition values:
       - In `/nix/store/dw8dg3hi01glv19rlfv9228s8dh1n6w1-source/scheduler_benchmark/nix/modules/kubernetes/master.nix': "k8s-master.cluster"
```

=> apparement il faut régler un problème de clé et de permissions, il faut que les clés soient créées au build time et le cluster doit être rejoind au runtime

2025.05.01 - OK - Diagnostic du cluster

```sh
[odancona@k8s-master:~]$ sudo -E kubectl cluster-info
Kubernetes control plane is running at https://k8s-master:6443
CoreDNS is running at https://k8s-master:6443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
                                                                               t
───────┬──────────────────────────────────────────────────────────────────────── 
       │ File: /var/lib/kubernetes/secrets/apitoken.secret
───────┼────────────────────────────────────────────────────────────────────────
   1   │ 145798dc80b4e7add931fcb9ccc37bf5
───────┴────────────────────────────────────────────────────────────────────────
```

=> I'm not sure what I'm missing ? the tricky part is that I need to build a part at build time and the other at runtime. And I'm not sure whether the problem is in the runtime or in the build time
=> Analyse avec Claude 3.7

```md
Your worker needs to properly locate and authenticate with the master. The main issues I see are:
- KUBECONFIG: The worker doesn't have a properly configured kubectl setup
- Node Join Process: The token-based join command needs more details
- Hostname Resolution: The worker may not be able to resolve "k8s-master"
```

=> déclaré Kubeconfig dans l'environnement mais il y a toujours le problème qu'il faut être sudo pour avoir les clés
=> pour le hostname j'ai changé en k8s-master pour le hostname et k8s-master.local dans kube
2025.05.01 - NOK - Impossible de rejoindre le cluster

=>

```sh
[odancona@nixos:~]$ cat apitoken.secret | sudo nixos-kubernetes-node-join
Restarting certmgr...
Job for certmgr.service failed because the control process exited with error code.
See "systemctl status certmgr.service" and "journalctl -xeu certmgr.service" for details.
```

```sh
[odancona@nixos:~]$ systemctl status certmgr.service
● certmgr.service - certmgr
     Loaded: loaded (/etc/systemd/system/certmgr.service; enabled; preset: igno>
     Active: activating (start-pre) since Thu 2025-05-01 18:12:58 UTC; 35s ago
 Invocation: 828357b901c847f0a0de07e8aef49dbc
  Cntrl PID: 7746 (certmgr-pre-sta)
         IP: 0B in, 300B out
         IO: 0B read, 0B written
      Tasks: 9 (limit: 4681)
     Memory: 4M (peak: 4.3M)
        CPU: 16ms
     CGroup: /system.slice/certmgr.service
             ├─7746 /nix/store/0irlcqx2n3qm6b1pc9rsd2i8qpvcccaj-bash-5.2p37/bin>
             └─7748 /nix/store/ph3q5yqb0b40v0a01dvw7ikah1x8xlw8-certmgr-3.0.3/b>

May 01 18:12:58 nixos systemd[1]: Failed to start certmgr.
May 01 18:12:58 nixos systemd[1]: certmgr.service: Consumed 28ms CPU time, 4.2M>
May 01 18:13:08 nixos systemd[1]: certmgr.service: Scheduled restart job, resta>
May 01 18:13:08 nixos systemd[1]: Starting certmgr...
May 01 18:13:08 nixos certmgr-pre-start[7748]: time="2025-05-01T18:13:08Z" leve>
May 01 18:13:08 nixos certmgr-pre-start[7748]: time="2025-05-01T18:13:08Z" leve>
May 01 18:13:08 nixos certmgr-pre-start[7748]: time="2025-05-01T18:13:08Z" leve>
```

```sh
[odancona@nixos:~]$ journalctl -xeu certmgr.service
░░ Subject: Resources consumed by unit runtime
░░ Defined-By: systemd
░░ Support: https://lists.freedesktop.org/mailman/listinfo/systemd-devel
░░ 
░░ The unit certmgr.service completed and consumed the indicated resources.
May 01 18:13:48 nixos systemd[1]: certmgr.service: Scheduled restart job, resta>
░░ Subject: Automatic restarting of a unit has been scheduled
░░ Defined-By: systemd
░░ Support: https://lists.freedesktop.org/mailman/listinfo/systemd-devel
░░ 
░░ Automatic restarting of the unit certmgr.service has been scheduled, as the >
░░ the configured Restart= setting for the unit.
May 01 18:13:48 nixos systemd[1]: Starting certmgr...
░░ Subject: A start job for unit certmgr.service has begun execution
░░ Defined-By: systemd
░░ Support: https://lists.freedesktop.org/mailman/listinfo/systemd-devel
░░ 
░░ A start job for unit certmgr.service has begun execution.
░░ 
░░ The job identifier is 32687.
May 01 18:13:48 nixos certmgr-pre-start[8213]: time="2025-05-01T18:13:48Z" leve>
May 01 18:13:48 nixos certmgr-pre-start[8213]: time="2025-05-01T18:13:48Z" leve>
May 01 18:13:48 nixos certmgr-pre-start[8213]: time="2025-05-01T18:13:48Z" leve>
```

```sh
sudo journalctl -u kubelet -f
...
May 01 18:15:29 nixos systemd[1]: Started Kubernetes Kubelet Service.
May 01 18:15:29 nixos kubelet[9389]: Flag --pod-infra-container-image has been deprecated, will be removed in a future release. Image garbage collector will get sandbox image information from CRI.
May 01 18:15:29 nixos kubelet[9389]: I0501 18:15:29.753870    9389 server.go:211] "--pod-infra-container-image will not be pruned by the image garbage collector in kubelet and should also be set in the remote runtime"
May 01 18:15:29 nixos kubelet[9389]: E0501 18:15:29.757488    9389 run.go:72] "command failed" err="failed to construct kubelet dependencies: unable to load client CA file /var/lib/kubernetes/secrets/ca.pem: error creating pool from /var/lib/kubernetes/secrets/ca.pem: data does not contain any valid RSA or ECDSA certificates"
May 01 18:15:29 nixos systemd[1]: kubelet.service: Main process exited, code=exited, status=1/FAILURE
May 01 18:15:29 nixos systemd[1]: kubelet.service: Failed with result 'exit-code'.
```

=> J'ai plein d'erreurs. Il faut absolument que easy cert fonctionne autrement le Kubernetes API server (kube-apiserver) ne démarre même plus.  On peut check avec la commande: `nc -vz k8s-master.local 6443`
=> inspection du module kubernetes nix apiserver.nix conclusion:
=> . Conditions pour que les certs soient générés

1. Il faut que services.kubernetes soit activé (tu l’as via roles = ["master"];).
2. Il faut que easyCerts = true (c’est le cas dans ta config).
3. Il ne doit pas déjà y avoir des certs dans /var/lib/kubernetes/secrets (sinon ils ne sont pas régénérés).
4. Les dossiers doivent exister et être accessibles (droits d’écriture pour root/kubernetes).
=> Le problème est maintenant clair :

Il manque la quasi-totalité des certificats dans /var/lib/kubernetes/secrets/ sur le master, alors que easyCerts = true.
=> Isolation des changements et oui le problème c'est d'avoir ajouté .local dans l'image du master ça casse les certificats:
Avant : masterAddress = "k8s-master" → tout fonctionne, les secrets sont générés.
Après : masterAddress = "k8s-master.local" → plus de secrets générés.
=>

```txt
Si cfg.masterAddress est une valeur qui ne peut pas être résolue localement lors du build de l’image (par exemple : k8s-master.local alors que le build n’a pas de mDNS), alors la génération du certificat peut échouer silencieusement, car openssl ou le script de génération tente peut-être de résoudre ce nom (pour l’ajouter dans le SAN ou autre), et échoue.
```

=> Il faut absolument bien placer la config à son bon endroit. Si on utilise le hostname partout, pour la génération des certificats ça plantera mais pour le runtime ça fonctionnera ou l'inverse. Donc on doit bien séparer les deux.

2025.05.01 - NOK - Impossible de configurer le cluster

```sh
[odancona@k8s-master:~]$ sudo journalctl -u kube-apiserver -f
May 01 22:10:47 k8s-master systemd[1]: kube-apiserver.service: Scheduled restart job, restart counter is at 771.
May 01 22:10:47 k8s-master systemd[1]: Started Kubernetes APIServer Service.
May 01 22:10:47 k8s-master kube-apiserver[11862]: Error: invalid argument "k8s-master.local" for "--advertise-address" flag: failed to parse IP: "k8s-master.local"
May 01 22:10:47 k8s-master systemd[1]: kube-apiserver.service: Main process exited, code=exited, status=1/FAILURE

[odancona@k8s-master:~]$ ping k8s-master
PING k8s-master (::1) 56 data bytes
64 bytes from localhost (::1): icmp_seq=1 ttl=64 time=0.061 ms
64 bytes from localhost (::1): icmp_seq=2 ttl=64 time=0.039 ms
```

=> donc le worker doit accéder à k8s-master.local mais le master doit être configuré avec k8s-master
=> j'enlève le hostNameFQDN du apiserver dans le master et rebuild le tout
=> Fonctionne sur le master mais pas sur le worker
=> Le kube-apiserver sur le master est bien starté c'est sûr:

```sh
[odancona@nixos:~]$ nc -vz k8s-master.local 6443
Connection to k8s-master.local (192.168.222.203) 6443 port [tcp/sun-sr-https] succeeded!
```

=> C'est un problème de certificat

```sh
failed to verify certificate: x509: certificate is valid for k8s-master, not k8s-master.local
```

=> Pourtant sur le master le certificat de l’API server est correct

```sh
nix-shell -p openssl --run 'openssl x509 -in /var/lib/kubernetes/secrets/kube-apiserver.pem -noout -text | grep DNS'
DNS:kubernetes, DNS:kubernetes.default.svc, DNS:kubernetes.default.svc.cluster.local, DNS:, DNS:k8s-master, DNS:k8s-master.local, IP Address:10.0.0.1, IP Address:127.0.0.1
```

=> On continue le diagnostic sur le worker (potentiellement flannel)

```sh
[odancona@nixos:~]$ getent hosts k8s-master.local
192.168.222.203 k8s-master.local

[odancona@k8s-master:~]$ sudo ss -ltnp | grep 8888
LISTEN 0      4096               *:8888             *:*    users:(("cfssl",pid=926,fd=3))           

[odancona@k8s-master:~]$ sudo netstat -ltnp | grep 8888
tcp6       0      0 :::8888                 :::*                    LISTEN      926/cfssl 

[odancona@nixos:~]$ nix-shell -p openssl --run 'openssl s_client -connect k8s-master.local:8888'

```

=> Le problème concerne le service cfssl (port 8888), pas le kube-apiserver (6443).
=> Le certificat présenté par cfssl a CN=k8s-master et ne contient PAS k8s-master.local dans ses SANs.
=> Il faut également configurer le SAN du certificat pour flannel
=> On creuse dans le code source de flannel.nix

```nix
services.kubernetes.pki.certs = {
  flannelClient = top.lib.mkCert {
    name = "flannel-client";
    CN = "flannel-client";
    action = "systemctl restart flannel.service";
  };
};
```

On va ajouter une variable hosts afin d'injecter des SANs personnalisés dans le certificat de flannel-client depuis ma config utilisateur (ici master.nix) ?

2025.05.01 - NOK - Echec de l'ajout du worker node

=> on master `sudo cat /var/lib/kubernetes/secrets/apitoken.secret`
=> on worker `echo 2e9f8d64a5ad92d63d3533adef75a64c | sudo nixos-kubernetes-node-join`
=> error

```sh
sudo journalctl -u certmgr --no-pager --output=cat
Starting certmgr...
time="2025-05-01T23:33:51Z" level=info msg="manager: loading certificates from /nix/store/826ikyn9m2z53wmd753z4h1lfc87b1kg-certmgr.d"
time="2025-05-01T23:33:51Z" level=info msg="manager: loading spec from /nix/store/826ikyn9m2z53wmd753z4h1lfc87b1kg-certmgr.d/flannelClient.json"
time="2025-05-01T23:33:51Z" level=warning msg="spec /nix/store/826ikyn9m2z53wmd753z4h1lfc87b1kg-certmgr.d/flannelClient.json does not specify key usage, defaulting to \"server auth\""
time="2025-05-01T23:33:51Z" level=error msg="managed: failed loading spec from /nix/store/826ikyn9m2z53wmd753z4h1lfc87b1kg-certmgr.d/flannelClient.json: {\"code\":7400,\"message\":\"failed POST to https://k8s-master.local:8888/api/v1/cfssl/info: Post \\\"https://k8s-master.local:8888/api/v1/cfssl/info\\\": tls: failed to verify certificate: x509: certificate is valid for k8s-master, not k8s-master.local\"}"
time="2025-05-01T23:33:51Z" level=error msg="stopping directory scan due to {\"code\":7400,\"message\":\"failed POST to https://k8s-master.local:8888/api/v1/cfssl/info: Post \\\"https://k8s-master.local:8888/api/v1/cfssl/info\\\": tls: failed to verify certificate: x509: certificate is valid for k8s-master, not k8s-master.local\"}"
time="2025-05-01T23:33:51Z" level=error msg="Failed: {\"code\":7400,\"message\":\"failed POST to https://k8s-master.local:8888/api/v1/cfssl/info: Post \\\"https://k8s-master.local:8888/api/v1/cfssl/info\\\": tls: failed to verify certificate: x509: certificate is valid for k8s-master, not k8s-master.local\"}"
certmgr.service: Control process exited, code=exited, status=1/FAILURE
certmgr.service: Failed with result 'exit-code'.
Failed to start certmgr.
```

=> Observations
Le certificat flannel-client.pem n’a que DNS:flannel-client dans ses SANs.
Le service cfssl du master utilise /var/lib/cfssl/cfssl.pem (pas le cert flannel-client).
Le cert présenté sur le port 8888 a pour CN k8s-master, pas flannel-client.
=> Etape suivante: Ajoute k8s-master.local (et k8s-master) dans le SAN du certificat utilisé par cfssl (/var/lib/cfssl/cfssl.pem), pas celui de flannel-client, puis redémarre cfssl.

2025.05.01 - OK - Cluster rejoint avec succès

=> on master `sudo cat /var/lib/kubernetes/secrets/apitoken.secret`
=> on worker `echo 2e9f8d64a5ad92d63d3533adef75a64c | sudo nixos-kubernetes-node-join`

2025.05.02 - NOK - Tentative d'automatisation de la configuration runtime
=> J'ai fait un script python mais je n'arrive pas à me connecter à la VM directement depuis X1-Carbon, je vais d'abord essayer de le faire manuellement
2025.05.02 - OK - Test de la connexion SSH
=> J'ai réussi à me connecter à la VM avec les commande suivante
`ssh -i ~/.ssh/rhodey odancona@192.168.222.182` => fonctionne uniquement depuis Rhodey car X1-Carbon n'a pas accès sur le scheduler_benchmark_netd

=> `ssh -J odancona@rhodey.lbl.gov odancona@192.168.222.182` ok
=> `ssh -J odancona@rhodey.lbl.gov odancona@k8s-master.local` ok
2025.05.02 - NOK - Impossible de se connecter à la VM avec le script python
=> Paramiko n'aime pas le jump
=> Création d'un wrapper pour tester la connexion SSH avec attente exponentielle
=> Le wrapper a du mal à se connecter à la VM avec le jump
=> Test d'une configuration manuelle dans le fichier ssh-config de X1-Carbon

2025.05.02 - OK - Création d'un alias SSH dans ~/.ssh/config

=> J'ai créé un alias SSH pour me connecter aux VMs facilement:

```yml
Host k8s-master
  HostName k8s-master.local
  User odancona
  ProxyJump odancona@rhodey
  IdentityFile ~/.ssh/rhodey

Host 192.168.222.*
  User odancona
  ProxyJump odancona@rhodey
  IdentityFile ~/.ssh/rhodey
```

2025.05.02 - NOK - Impossible de se connecter à la VM avec le script python

=> La VM n’a pas de ~/.ssh/authorized_keys pour odancona malgré ta config NixOS.
=> Pas un problème car la clé publique est bien dans l'autre directory : /etc/ssh/authorized_keys.d/odancona
=> Le problème vient plus de la clé privé qui n'est pas présente sur Rhodey

```sh
odancona@rhodey:~$ ssh -i /home/odancona/.ssh/rhodey odancona@192.168.222.154
Warning: Identity file /home/odancona/.ssh/rhodey not accessible: No such file or directory.
```

=> ça fonctionne depuis le laptop car j'utilise ProxyJump qui fait le tunnel pour moi donc la connexion part de mon laptop.
=> Il manquait expanduser() sur le chemin de la clé privée. Ainsi, Paramiko n'arrivait pas à établir la connexion SSH.

2025.05.02 - NOK - Impossible de se connecter à la VM avec le script python

=> Il faut gérer le password correctement

```sh
[2025-05-02 14:42:34,291][__main__][ERROR] - Error provisioning cluster: Error executing command on 192.168.222.236: 
We trust you have received the usual lecture from the local System
Administrator. It usually boils down to these three things:

    #1) Respect the privacy of others.
    #2) Think before you type.
    #3) With great power comes great responsibility.

For security reasons, the password you type will not be visible.

sudo: a terminal is required to read the password; either use the -S option to read from standard input or configure an askpass helper
sudo: a password is required
```

=> désactivation du mdp dans la vm

2025.05.02 - OK - Configuration du cluster kubernetes automatique OK test avec plusieurs workers
2025.05.02 - NOK - Impossible d'ajouter plusieurs workers.

=> Vu que les workers ont le même nom d'host, il y a un problème de collision et il y a un seul worker qui est ajouté au cluster. Si tes deux VMs (“compute-node-1” et “compute-node-2”) démarrent avec la même image NixOS et que cette image a un hostname statique (par exemple nixos), alors : K8s ne petu pas distinguer les noeuds et le dernier qui s'enregistre remplace l'autre.
=> Comme j'utilise un template d’image, il faut que le hostname soit personnalisé à la création de la VM.
=> Fix simple, changer le hostname à la volée

```py
self.ssh_execute(ip, f"sudo hostnamectl set-hostname {node_config.name}")
```

=> ou pas: Could not set pretty hostname: Changing system settings via systemd is not supported on NixOS.
=> On va forcer le hostname manuellement et redémarrer les services
=>

```py
self.ssh_execute(ip, f"echo '{node_config.name}' | sudo tee /etc/hostname && sudo hostname {node_config.name}")
self.ssh_execute(ip, "sudo systemctl restart kubelet")
self.ssh_execute(ip, "sudo systemctl restart avahi-daemon flannel kube-proxy")
```

=> Fail Même si tu changes le hostname en RAM, Avahi continue d’utiliser celui défini dans sa conf au lancement.
=> Fail Même si tu changes le hostname dans le NixStore (il faut le démonter et remonter en écriture car il est en lecture seul), Avahi continue d’utiliser celui défini dans sa conf au lancement.
=> On va tenter de forcer K8s d'ajouter le hostname manuellement avec `--hostname-override=compute-node-1`
=> Ne fonctionne pas car il faut le préciser sur la config Nix au moment du build !
=>

```txt
Comment avoir une image générique, mais injecter dynamiquement le hostname (et autres paramètres) à la création de la VM, sans builder une image par node ?
```

=> Il faut vraiment rebuild switch ou créer une image par worker

2025.05.05 - NOK - Impossible de reconfigurer le cluster

=> Il fallait simplement attendre que le master soit prêt un petit sleep 10 fonctionne très bien
2025.05.05 - NOK - Reconfiguration du flake. Afin de pouvoir faire un nixos-rebuild switch, il faut charger la configuration sur la vm. Pour ceci il faut modifier le flakes.

=> Ajout de specialArgs = { self = self; }; et system.activationScripts.saveFlakeConfig;
=>

```sh
[odancona@k8s-master:~]$ nixos-rebuild switch --flake /etc/nixos/current-systemconfig
error: flake 'path:/etc/nixos/current-systemconfig' does not provide attribute 'packages.x86_64-linux.nixosConfigurations."k8s-master".config.system.build.nixos-rebuild', 'legacyPackages.x86_64-linux.nixosConfigurations."k8s-master".config.system.build.nixos-rebuild' or 'nixosConfigurations."k8s-master".config.system.build.nixos-rebuild'

[odancona@k8s-master:~]$ tree /etc/nixos/current-systemconfig/
/etc/nixos/current-systemconfig/
├── flake.lock
├── flake.nix
├── lazy.sh
├── modules
│   └── kubernetes
│       ├── master.nix
│       └── worker.nix
└── vm-config.nix

```

=> Ajout de l'export de configuration au flake + factorisation
=>

```sh
[odancona@k8s-master:~]$ nixos-rebuild switch --flake /etc/nixos/current-systemconfig
building the system configuration...
error:
       … while calling the 'head' builtin
         at /nix/store/fnyp8nbpm5dlxbqdq9md4jdww3ga3hjl-source/lib/attrsets.nix:1574:11:
         1573|         || pred here (elemAt values 1) (head values) then
         1574|           head values
             |           ^
         1575|         else

       … while evaluating the attribute 'value'
         at /nix/store/fnyp8nbpm5dlxbqdq9md4jdww3ga3hjl-source/lib/modules.nix:816:9:
          815|     in warnDeprecation opt //
          816|       { value = addErrorContext "while evaluating the option `${showOption loc}':" value;
             |         ^
          817|         inherit (res.defsFinal') highestPrio;

       … while evaluating the option `system.build.toplevel':

       … while evaluating definitions from `/nix/store/fnyp8nbpm5dlxbqdq9md4jdww3ga3hjl-source/nixos/modules/system/activation/top-level.nix':

       (stack trace truncated; use '--show-trace' to show the full, detailed trace)

       error:
       Failed assertions:
       - The ‘fileSystems’ option does not specify your root file system.
```

=> apparement, le filesystem n'est correctement spécifié

```md
Quand tu fais un nixos-rebuild switch, Nix essaie de recompiler le système depuis le flake. Pour cela, il doit pouvoir "monter" le root filesystem dans la configuration, ce qui n'est pas nécessaire quand tu utilises nixos-generators pour faire une image qcow2, mais obligatoire pour un nixosSystem (comme utilisé par nixos-rebuild).

Tu exécutes une VM NixOS générée par nixos-generators avec une image disque minimale (qcow2). Cette image n’a pas de fileSystems."/" explicite, donc Nix ne peut pas reconstruire le système (nixos-rebuild switch) depuis l’intérieur de la VM car il ne sait pas quelle est sa racine.
```

=> Solution : Ajouter fileSystems."/" à ton flake pour déverrouiller nixos-rebuild
=>

```sh
       error: The option fileSystems."/".device' has conflicting definition values:
       - In /nix/store/a59nywcf635014w55rhzddgajjd2rz2r-source/scheduler_benchmark/nix/vm-config.nix': "/dev/vda3"
       - In /nix/store/zfr9q0312byaiphnmdknqj792aci3654-source/formats/qcow.nix': "/dev/disk/by-label/nixos"
       Use lib.mkForce value or lib.mkDefault value to change the priority on any of these definitions.
```

=> Il faut forcer le filesystem dans le flake.nix
=>

```sh
[odancona@nixos:~]$ nixos-rebuild switch --flake /etc/nixos/current-systemconfig
error: flake 'path:/etc/nixos/current-systemconfig' does not provide attribute 'packages.x86_64-linux.nixosConfigurations."nixos".config.system.build.nixos-rebuild', 'legacyPackages.x86_64-linux.nixosConfigurations."nixos".config.system.build.nixos-rebuild' or 'nixosConfigurations."nixos".config.system.build.nixos-rebuild'
```

=> `sudo nixos-rebuild switch --flake /etc/nixos/current-systemconfig#k8s-worker`
=> Success

2025.05.06 - NOK - Il faut trouver un moyen de rebuild le flake avec le nouveau hostname
=> Absolument horrible mais ça fonctionne à la mano

```py
 # Write config
cmd_make_nix_config = f"sed -i 's|^  #networking\.hostName = .*;|  networking.hostName = \"{node_config.name}\";|' /etc/nixos/current-systemconfig/modules/kubernetes/worker.nix"
self.ssh_execute(ip, cmd_make_nix_config)

# nixos-rebuild switch
cmd_nixos_rebuild = "sudo nixos-rebuild switch --flake /etc/nixos/current-systemconfig#k8s-worker"
```

=>

```sh
[2025-05-06 15:48:52,236][scheduler_benchmark.vm.provision][ERROR] - Error executing command sudo nixos-rebuild switch --flake /etc/nixos/current-systemconfig#k8s-worker on 192.168.222.193
...
