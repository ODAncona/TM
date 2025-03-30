import libvirt
import os
import time
import tempfile
from scheduler_benchmark.models import NodeConfig, Resource, ResourceType

class LibvirtConnection:
    def __init__(self, hostname: str, username: str | None = None, 
                 identity_file: str | None = None):
        self.hostname = hostname
        self.username = username
        self.identity_file = identity_file
        self.ssh_config_file = None
        self.conn = None
        
    def __enter__(self):
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        
    def _create_ssh_config(self):
        """Create a temporary SSH config file to force key-based authentication"""
        if not self.identity_file:
            return None
            
        expanded_identity = os.path.expanduser(self.identity_file)
        
        # Create temporary SSH config file
        ssh_config_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        ssh_config_file.write(f"""Host {self.hostname}
    IdentityFile {expanded_identity}
    PasswordAuthentication no
    PubkeyAuthentication yes
    BatchMode yes
    StrictHostKeyChecking no
""")
        ssh_config_file.close()
        return ssh_config_file.name
        
    def connect(self):
        if not self.conn:
            # Create SSH config
            if self.identity_file:
                self.ssh_config_file = self._create_ssh_config()
                expanded_identity = os.path.expanduser(self.identity_file)
                
                # Configure libvirt SSH environment
                uri = f"qemu+ssh://{self.username}@{self.hostname}/system?no_verify=1&keyfile={expanded_identity}&no_tty=1"
                os.environ["LIBVIRT_DEFAULT_URI"] = uri
                os.environ["LIBVIRT_SSH_KEY"] = expanded_identity
                os.environ["LIBVIRT_SSH_CONFIG"] = self.ssh_config_file
                
                # Connect using the specified URI
                self.conn = libvirt.open(uri)
            else:
                # Standard connection without SSH key
                uri = f"qemu+ssh://{self.username}@{self.hostname}/system"
                self.conn = libvirt.open(uri)
                
        return self.conn
        
    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            
        # Clean up temporary SSH config file
        if self.ssh_config_file and os.path.exists(self.ssh_config_file):
            os.unlink(self.ssh_config_file)
            self.ssh_config_file = None
            
    def get_vm(self, name: str) -> libvirt.virDomain | None :
        """Get a VM by name"""
        try:
            return self.conn.lookupByName(name)
        except libvirt.libvirtError:
            return None
            
    def vm_exists(self, name: str) -> bool:
        """Check if a VM exists"""
        return self.get_vm(name) is not None
        
    def create_volume(self, name: str, size_gb: int, 
                      base_image: str | None = None,
                      pool_name: str = "default") -> str:
        """Create a new volume, optionally based on an image"""
        size_bytes = size_gb * 1024 * 1024 * 1024
        
        # Get storage pool
        pool = self.conn.storagePoolLookupByName(pool_name)
        
        if base_image:
            # Create volume from base image
            vol_xml = f"""
            <volume>
                <name>{name}</name>
                <capacity unit="bytes">{size_bytes}</capacity>
            </volume>
            """
            base_vol = pool.storageVolLookupByName(base_image)
            volume = pool.createXMLFrom(vol_xml, base_vol, 0)
        else:
            # Create empty volume
            vol_xml = f"""
            <volume>
                <name>{name}</name>
                <capacity unit="bytes">{size_bytes}</capacity>
                <target>
                    <format type="qcow2"/>
                </target>
            </volume>
            """
            volume = pool.createXML(vol_xml, 0)
            
        return volume.path()
    
    def create_vm(self, node_config: NodeConfig, 
                  cloud_init_iso: str, 
                  base_image: str | None = None) -> tuple[libvirt.virDomain, str]:
        """Create a VM based on node configuration"""
        # Create volume
        volume_path = self.create_volume(
            f"{node_config.name}_disk", 
            node_config.disk_size_gb,
            base_image
        )
        
        # Calculate resources
        memory_mb = 0
        vcpus = 0
        
        for res in node_config.resources:
            if res.type == ResourceType.RAM:
                memory_mb = res.amount
            elif res.type == ResourceType.CPU:
                vcpus = res.amount
                
        if memory_mb == 0:
            memory_mb = 2048  # Default value
        if vcpus == 0:
            vcpus = 1  # Default value
            
        # Create VM XML
        vm_xml = f"""
        <domain type='kvm'>
            <name>{node_config.name}</name>
            <memory unit='MiB'>{memory_mb}</memory>
            <vcpu>{vcpus}</vcpu>
            <os>
                <type arch='x86_64'>hvm</type>
                <boot dev='hd'/>
            </os>
            <devices>
                <disk type='file' device='disk'>
                    <driver name='qemu' type='qcow2'/>
                    <source file='{volume_path}'/>
                    <target dev='vda' bus='virtio'/>
                </disk>
                <disk type='file' device='cdrom'>
                    <driver name='qemu' type='raw'/>
                    <source file='{cloud_init_iso}'/>
                    <target dev='hda' bus='ide'/>
                    <readonly/>
                </disk>
                <interface type='network'>
                    <source network='{node_config.network.name}'/>
                    <model type='virtio'/>
                </interface>
                <console type='pty'>
                    <target type='serial' port='0'/>
                </console>
                <graphics type='spice' autoport='yes' listen='127.0.0.1'>
                    <listen type='address' address='127.0.0.1'/>
                </graphics>
            </devices>
        </domain>
        """
        
        domain = self.conn.defineXML(vm_xml)
        domain.create()
        
        # Get IP address (may take some time)
        ip_address = None
        for _ in range(30):  # try for 30 seconds
            try:
                ifaces = domain.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE)
                for _, data in ifaces.items():
                    for addr in data.get('addrs', []):
                        if addr['type'] == libvirt.VIR_IP_ADDR_TYPE_IPV4:
                            ip_address = addr['addr']
                            break
                if ip_address:
                    break
            except libvirt.libvirtError:
                pass
            time.sleep(1)
            
        return domain, ip_address
        
    def delete_vm(self, name: str, delete_storage: bool = True) -> bool:
        """Delete a VM and optionally its storage"""
        domain = self.get_vm(name)
        if not domain:
            return False
            
        # Get disks before shutting down
        disks = []
        if delete_storage:
            xml = domain.XMLDesc()
            # Simple parsing - in production code use proper XML parsing
            for line in xml.split('\n'):
                if "<source file='" in line and "cdrom" not in line:
                    disk_path = line.split("'")[1]
                    disks.append(disk_path)
        
        # Shutdown VM if running
        if domain.isActive():
            domain.destroy()
            
        # Undefine VM
        domain.undefineFlags(libvirt.VIR_DOMAIN_UNDEFINE_NVRAM)
        
        # Delete storage
        if delete_storage:
            for disk_path in disks:
                try:
                    vol = self.conn.storageVolLookupByPath(disk_path)
                    vol.delete(0)
                except libvirt.libvirtError:
                    pass
                    
        return True