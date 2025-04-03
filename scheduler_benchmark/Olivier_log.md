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

```
wget -O /home/odancona/.local/share/libvirt/images/ubuntu-24.04-server-cloudimg-amd64.img https://cloud-images.ubuntu.com/releases/24.04/release/ubuntu-24.04-server-cloudimg-amd64.img
```

2025.04.02 - NOK - Problème d'accès au fichier image de la VM. Impossible même après avoir créé une pool de retrouver l'image de la VM même si elle existe.
2025.04.02 - OK - Création d'un fichier de création de configuration NIX.
