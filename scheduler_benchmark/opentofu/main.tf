variable "cluster_name" {
  type = string
}

variable "nodes" {
  type = list(object({
    name       = string
    cpu        = number
    memory_mb  = number
    disk_gb    = number
  }))
}

variable "libvirt_url" {
  type = string
}

# ...
# Terraform resources referencing these variables
# Example snippet:
provider "libvirt" {
  uri = var.libvirt_url
}

resource "libvirt_domain" "head_nodes" {
  count        = length(var.nodes)
  name         = var.nodes[count.index].name
  memory       = var.nodes[count.index].memory_mb
  vcpu         = var.nodes[count.index].cpu
  # ...
}
