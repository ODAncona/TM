import libvirt
import os
import time
import tempfile
from scheduler_benchmark.models import NodeConfig, Resource, ResourceType
import logging

class LibvirtConnection:
    def __init__(
        self,
        hostname: str,
        username: str | None = None,
        identity_file: str | None = None,
        pool_name: str = "default",
        logger: logging.Logger | None = None,
    ):
        self.hostname = hostname
        self.username = username
        self.identity_file = identity_file
        self.ssh_config_file = None
        self.conn = None
        self.pool_name = pool_name
        self.logger = logger or logging.getLogger(__name__)

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
        self.logger.debug(f"Création d'un fichier de configuration SSH avec la clé {expanded_identity}")

        # Create temporary SSH config file
        ssh_config_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
        ssh_config_file.write(
            f"""Host {self.hostname}
    IdentityFile {expanded_identity}
    PasswordAuthentication no
    PubkeyAuthentication yes
    BatchMode yes
    StrictHostKeyChecking no
    """
        )
        ssh_config_file.close()
        self.logger.debug(f"Fichier de configuration SSH créé: {ssh_config_file.name}")
        return ssh_config_file.name

    def connect(self):
        if not self.conn:
            self.logger.info(f"Connexion à l'hôte libvirt {self.hostname}")
            try:
                # Create SSH config
                if self.identity_file:
                    self.ssh_config_file = self._create_ssh_config()
                    expanded_identity = os.path.expanduser(self.identity_file)

                    # Configure libvirt SSH environment
                    uri = f"qemu+ssh://{self.username}@{self.hostname}/system?no_verify=1&keyfile={expanded_identity}&no_tty=1"
                    os.environ["LIBVIRT_DEFAULT_URI"] = uri
                    os.environ["LIBVIRT_SSH_KEY"] = expanded_identity
                    os.environ["LIBVIRT_SSH_CONFIG"] = self.ssh_config_file
                    
                    self.logger.debug(f"Utilisation de l'URI: {uri}")

                    # Connect using the specified URI
                    self.conn = libvirt.open(uri)
                else:
                    # Standard connection without SSH key
                    uri = f"qemu+ssh://{self.username}@{self.hostname}/system"
                    self.logger.debug(f"Utilisation de l'URI standard: {uri}")
                    self.conn = libvirt.open(uri)
                    
                self.logger.info(f"Connexion réussie à {self.hostname}")
            except libvirt.libvirtError as e:
                self.logger.error(f"Échec de connexion à {self.hostname}: {str(e)}")
                raise

        return self.conn

    def disconnect(self):
        if self.conn:
            self.logger.info(f"Déconnexion de l'hôte libvirt {self.hostname}")
            self.conn.close()
            self.conn = None

        # Clean up temporary SSH config file
        if self.ssh_config_file and os.path.exists(self.ssh_config_file):
            self.logger.debug(f"Suppression du fichier de configuration SSH temporaire: {self.ssh_config_file}")
            os.unlink(self.ssh_config_file)
            self.ssh_config_file = None
    
    def get_vm(self, name: str) -> libvirt.virDomain | None:
        """Get a VM by name"""
        try:
            vm = self.conn.lookupByName(name)
            self.logger.debug(f"VM '{name}' trouvée")
            return vm
        except libvirt.libvirtError:
            self.logger.debug(f"VM '{name}' non trouvée")
            return None

    def vm_exists(self, name: str) -> bool:
        """Check if a VM exists"""
        return self.get_vm(name) is not None

    def create_volume(
        self, name: str, size_gb: int, base_image: str | None = None
    ) -> str:
        """Create a new volume, optionally based on an image"""
        if self.conn is None:
            self.logger.error("Tentative de création de volume sans connexion établie")
            raise RuntimeError("Not connected to libvirt")

        size_bytes = size_gb * 1024 * 1024 * 1024
        self.logger.info(f"Création du volume '{name}' de {size_gb}GB" + (f" basé sur '{base_image}'" if base_image else ""))

        # Get storage pool
        try:
            pool = self.conn.storagePoolLookupByName(self.pool_name)
        except libvirt.libvirtError as e:
            self.logger.error(f"Impossible de trouver le pool de stockage '{self.pool_name}': {str(e)}")
            raise

        if base_image:
            try:
                # Try to use as volume name in pool (standard approach)
                base_vol = pool.storageVolLookupByName(base_image)
                self.logger.debug(f"Image de base '{base_image}' trouvée dans le pool")

                # Create volume from base image
                vol_xml = f"""
                <volume>
                    <name>{name}</name>
                    <capacity unit="bytes">{size_bytes}</capacity>
                    <target>
                        <format type="qcow2"/>
                    </target>
                </volume>
                """
                volume = pool.createXMLFrom(vol_xml, base_vol, 0)

            except libvirt.libvirtError as e:
                self.logger.warning(f"Base image '{base_image}' non trouvée dans le pool: {str(e)}")
                # If it's not in the pool, check if it's a full path on the remote system
                if os.path.isabs(base_image):
                    # For absolute paths, we can try to use the vol-create-from command
                    # which is what administrators typically use
                    error_msg = f"Base image '{base_image}' not found in pool '{self.pool_name}', but looks like a path. " \
                                f"Try importing it first with: virsh vol-create-as {self.pool_name} {os.path.basename(base_image)} --format qcow2"
                    self.logger.error(error_msg)
                    print(error_msg)

                # Fail with a helpful error message
                error_msg = f"Base image '{base_image}' not found in storage pool '{self.pool_name}'. " \
                            f"Please add it to the pool first using standard libvirt tools."
                self.logger.error(error_msg)
                raise ValueError(error_msg)
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

        volume_path = volume.path()
        self.logger.info(f"Volume '{name}' créé avec succès: {volume_path}")
        return volume_path

    def delete_volume(self, name: str) -> bool:
        """Delete a volume"""
        self.logger.info(f"Suppression du volume '{name}'")
        try:
            pool = self.conn.storagePoolLookupByName(self.pool_name)
            volume = pool.storageVolLookupByName(name)
            volume.delete(0)
            self.logger.info(f"Volume '{name}' supprimé avec succès")
            return True
        except libvirt.libvirtError as e:
            self.logger.warning(f"Échec de la suppression du volume '{name}': {str(e)}")
            return False

    def create_vm(
        self, node_config: NodeConfig, base_image: str | None = None, wait_time: int = 30
    ) -> tuple[libvirt.virDomain, str]:
        """Create a VM based on node configuration"""
        if self.conn is None:
            raise RuntimeError("Not connected to libvirt")
        # Create volume
        volume_path = self.create_volume(
            f"{node_config.name}_disk",
            node_config.disk_size_gb,
            base_image,
        )

        # Extract resources
        for res in node_config.resources:
            if res.type == ResourceType.RAM:
                memory_mb = res.amount
            elif res.type == ResourceType.CPU:
                vcpus = res.amount

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
        self.logger.info(f"VM {node_config.name} créée, en attente d'une adresse IP...")


        # Get IP address (may take some time)
        ip_address = None
        for _ in range(wait_time):
            try:
                ifaces = domain.interfaceAddresses(
                    libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE
                )
                for _, data in ifaces.items():
                    for addr in data.get("addrs", []):
                        if addr["type"] == libvirt.VIR_IP_ADDR_TYPE_IPV4:
                            ip_address = addr["addr"]
                            break
                if ip_address:
                    break
            except libvirt.libvirtError:
                pass
            time.sleep(1)

        return domain, ip_address

    def delete_vm(self, name: str, delete_storage: bool = True) -> bool:
        """Delete a VM and optionally its storage"""
        self.logger.info(f"Suppression de la VM '{name}'" + (" avec stockage" if delete_storage else ""))
        
        domain = self.get_vm(name)
        if not domain:
            self.logger.warning(f"VM '{name}' non trouvée")
            return False

        # Get disks before shutting down
        disks = []
        if delete_storage:
            xml = domain.XMLDesc()
            # Simple parsing - in production code use proper XML parsing
            for line in xml.split("\n"):
                if "<source file='" in line and "cdrom" not in line:
                    disk_path = line.split("'")[1]
                    disks.append(disk_path)
                    self.logger.debug(f"Disque trouvé à supprimer: {disk_path}")

        # Shutdown VM if running
        if domain.isActive():
            self.logger.debug(f"Arrêt forcé de la VM '{name}'")
            domain.destroy()

        # Undefine VM
        try:
            domain.undefineFlags(libvirt.VIR_DOMAIN_UNDEFINE_NVRAM)
            self.logger.debug(f"VM '{name}' supprimée de la configuration")
        except libvirt.libvirtError as e:
            self.logger.error(f"Erreur lors de la suppression de la VM '{name}': {str(e)}")
            return False

        # Delete storage
        if delete_storage:
            for disk_path in disks:
                try:
                    vol = self.conn.storageVolLookupByPath(disk_path)
                    vol.delete(0)
                    self.logger.debug(f"Disque supprimé: {disk_path}")
                except libvirt.libvirtError as e:
                    self.logger.warning(f"Impossible de supprimer le disque {disk_path}: {str(e)}")

        self.logger.info(f"VM '{name}' supprimée avec succès")
        return True