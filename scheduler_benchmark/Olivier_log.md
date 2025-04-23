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
