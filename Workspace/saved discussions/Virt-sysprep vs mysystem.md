# VMProvisioner vs virt-sysprep: Key Differences

The code in this project and `virt-sysprep` serve different but complementary purposes in VM management:

## Purpose
- **VMProvisioner**: Creates and manages VMs for scheduler benchmarking, focusing on provisioning complete clusters with specific configurations
- **virt-sysprep**: Prepares VM images for reuse by cleaning/resetting machine-specific details

## Primary Functions
- **VMProvisioner**:
  - Creates new VMs with specified resources (CPU, RAM, disk)
  - Provisions entire clusters with head and compute nodes
  - Configures networking and user access
  - Manages VM lifecycle (creation and deletion)

- **virt-sysprep**:
  - Resets/removes machine-specific details (hostnames, SSH keys, MAC addresses)
  - Removes user accounts and customizations
  - Clears logs, caches, and temporary files
  - Prepares images to be used as templates

## Workflow Relationship
These tools would typically be used in sequence:
1. **virt-sysprep** would prepare base images
2. **VMProvisioner** would use those base images to create configured VMs for benchmarking

## Integration
- **VMProvisioner** is a Python wrapper around libvirt integrated into a larger benchmarking system
- **virt-sysprep** is a standalone tool from the libguestfs toolkit

In essence, VMProvisioner is focused on creating and managing VMs with specific configurations for benchmarking, while virt-sysprep is focused on cleaning and preparing VM images for reuse.