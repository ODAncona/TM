terraform {
  required_providers {
    libvirt = {
      source = "dmacvicar/libvirt"
    }
  }
}

# Configure libvirt provider to connect to remote host rhodey via SSH
provider "libvirt" {
  uri = "qemu+ssh://odancona@rhodey.lbl.gov/session"
}

# Ubuntu 24.04 cloud image
resource "libvirt_volume" "ubuntu_24_04_cloud" {
  name   = "ubuntu-24.04-server-cloudimg-amd64.img"
  source = "https://cloud-images.ubuntu.com/releases/24.04/release/ubuntu-24.04-server-cloudimg-amd64.img"
  format = "qcow2"
  id = "/home/odancona/.local/share/libvirt/images"
}

# Create a volume for the VM using the cloud image as base
resource "libvirt_volume" "vm_volume" {
  name           = "ubuntu_24_04_vm_volume"
  base_volume_id = libvirt_volume.ubuntu_24_04_cloud.id
  size           = 16 * 1024 * 1024 * 1024  # 16GB
}

# Cloud-init config
data "template_file" "user_data" {
  template = <<-EOF
    #cloud-config
    hostname: vm-ubuntu-24
    ssh_pwauth: true
    users:
      - name: odancona
        sudo: ['ALL=(ALL) NOPASSWD:ALL']
        groups: sudo
        shell: /bin/bash
        ssh_authorized_keys:
          - ${file("~/.ssh/rhodey.pub")}
    growpart:
      mode: auto
      devices: ['/']
    runcmd:
      - resize2fs /dev/vda1
  EOF
}

resource "libvirt_cloudinit_disk" "cloudinit" {
  name      = "cloudinit.iso"
  user_data = data.template_file.user_data.rendered
}

# Define the VM
resource "libvirt_domain" "ubuntu_vm" {
  name   = "vm-ubuntu-24"
  memory = 2048
  vcpu   = 2

  cloudinit = libvirt_cloudinit_disk.cloudinit.id

  disk {
    volume_id = libvirt_volume.vm_volume.id
  }

  # Connect to the existing network
  network_interface {
    network_name   = "scheduler_benchmark_net"
    wait_for_lease = true
  }

  console {
    type        = "pty"
    target_port = "0"
    target_type = "serial"
  }

  graphics {
    type        = "spice"
    listen_type = "address"
    autoport    = true
  }
}

output "vm_ip" {
  value = libvirt_domain.ubuntu_vm.network_interface[0].addresses[0]
}