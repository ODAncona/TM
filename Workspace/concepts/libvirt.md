
The difference between "System" and "Session" connection types in libvirt is crucial:

- **System**: VMs run with system-level permissions, store images in system locations (like `/mnt/vmpool/vms/`) that require elevated privileges
- **Session**: VMs run with your user permissions, store images in your home directory (`~/.local/share/libvirt/images`)