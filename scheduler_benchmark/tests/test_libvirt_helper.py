import pytest
import uuid
import os
import tempfile
import libvirt
from pathlib import Path
from scheduler_benchmark.vm.libvirt_helper import LibvirtConnection
from scheduler_benchmark.models import NodeConfig, Resource, ResourceType, NetworkConfig, UserConfig

# Configuration pour la connexion au serveur libvirt rhodey
LIBVIRT_HOST = "rhodey.lbl.gov"
LIBVIRT_USER = "odancona"
LIBVIRT_IDENTITY = "~/.ssh/rhodey"
LIBVIRT_BASE_IMAGE = "ubuntu-24.04-server-cloudimg-amd64.img"
LIBVIRT_TEST_NETWORK = "scheduler_benchmark_net"

# Préfixe pour les ressources de test (éviter les collisions avec des ressources existantes)
TEST_PREFIX = "pytest_libvirt_"

@pytest.fixture()
def libvirt_connection():
    """Fixture qui fournit une connexion libvirt configurée pour les tests"""
    connection = LibvirtConnection(
        hostname=LIBVIRT_HOST,
        username=LIBVIRT_USER,
        identity_file=LIBVIRT_IDENTITY
    )
    
    # Connexion à libvirt
    connection.connect()
    
    # S'assurer que la connexion est établie
    assert connection.conn is not None, "Failed to establish libvirt connection"
    
    # Fournir la connexion aux tests
    yield connection
    
    # Fermer la connexion après les tests
    connection.disconnect()

@pytest.fixture
def unique_name():
    """Générer un nom unique pour les ressources de test"""
    return f"{TEST_PREFIX}{uuid.uuid4().hex[:8]}"

@pytest.fixture
def mock_cloud_init_iso():
    """Créer un fichier ISO fictif pour les tests"""
    iso_file = tempfile.NamedTemporaryFile(suffix=".iso", delete=False)
    iso_file.close()
    
    # Fournir le chemin
    yield iso_file.name
    
    # Nettoyer le fichier
    if os.path.exists(iso_file.name):
        os.unlink(iso_file.name)

@pytest.fixture
def test_node_config(unique_name):
    """Créer une configuration de nœud pour les tests"""
    return NodeConfig(
        name=unique_name,
        resources=[
            Resource(type=ResourceType.CPU, amount=1),
            Resource(type=ResourceType.RAM, amount=1024)
        ],
        network=NetworkConfig(
            name=LIBVIRT_TEST_NETWORK,
            cidr="192.168.122.0/24"
        ),
        user=UserConfig(
            name="testuser",
            sudo=True
        ),
        image="ubuntu",
        disk_size_gb=10
    )

def test_connection(libvirt_connection):
    """Vérifier que la connexion à libvirt fonctionne"""
    # La connexion est déjà établie par le fixture
    assert libvirt_connection.conn is not None
    
    # Vérifier quelques informations de base
    hostname = libvirt_connection.conn.getHostname()
    assert hostname, f"Impossible d'obtenir le hostname de l'hôte libvirt: {hostname}"
    
    hypervisor = libvirt_connection.conn.getType()
    assert hypervisor, f"Impossible d'obtenir le type d'hyperviseur: {hypervisor}"

def test_disconnect_and_reconnect(libvirt_connection):
    """Tester la déconnexion et la reconnexion"""
    # Déconnecter
    libvirt_connection.disconnect()
    assert libvirt_connection.conn is None
    
    # Reconnecter
    libvirt_connection.connect()
    assert libvirt_connection.conn is not None
    
    # Vérifier que la connexion fonctionne
    hostname = libvirt_connection.conn.getHostname()
    assert hostname

def test_get_vm_and_vm_exists(libvirt_connection):
    """Tester les méthodes get_vm et vm_exists"""
    # Obtenir la liste des VMs existantes
    domains = libvirt_connection.conn.listAllDomains()
    
    # S'assurer qu'il y a au moins une VM pour tester get_vm
    if domains:
        first_vm_name = domains[0].name()
        
        # Tester get_vm avec une VM existante
        vm = libvirt_connection.get_vm(first_vm_name)
        assert vm is not None
        assert vm.name() == first_vm_name
        
        # Tester vm_exists avec une VM existante
        assert libvirt_connection.vm_exists(first_vm_name) is True
    
    # Tester get_vm avec une VM inexistante
    non_existent_vm = f"{TEST_PREFIX}non_existent_vm"
    assert libvirt_connection.get_vm(non_existent_vm) is None
    
    # Tester vm_exists avec une VM inexistante
    assert libvirt_connection.vm_exists(non_existent_vm) is False

def test_create_and_delete_volume(libvirt_connection, unique_name):
    """Tester la création et la suppression d'un volume"""
    # Créer un nouveau volume
    volume_name = unique_name
    volume_size = 1  # 1 GB
    
    try:
        # Créer le volume
        volume_path = libvirt_connection.create_volume(volume_name, volume_size)
        
        # Vérifier que le volume a été créé
        assert volume_path, f"Le chemin du volume est vide: {volume_path}"
        
        # Vérifier que le volume existe en essayant de le récupérer
        pool = libvirt_connection.conn.storagePoolLookupByName("default")
        try:
            volume = pool.storageVolLookupByName(volume_name)
            assert volume is not None
        except libvirt.libvirtError:
            pytest.fail(f"Le volume {volume_name} n'a pas été créé correctement")
    
    finally:
        # Nettoyer: supprimer le volume
        try:
            pool = libvirt_connection.conn.storagePoolLookupByName("default")
            volume = pool.storageVolLookupByName(volume_name)
            volume.delete(0)
        except (libvirt.libvirtError, UnboundLocalError):
            pass  # Le volume n'existe peut-être pas, ignorer l'erreur

def test_create_volume_from_base_image(libvirt_connection, unique_name):
    """Tester la création d'un volume à partir d'une image de base"""
    # Créer un nouveau volume basé sur l'image existante
    volume_name = unique_name
    volume_size = 10  # 10 GB
    
    try:
        # Vérifier d'abord que l'image de base existe
        pool = libvirt_connection.conn.storagePoolLookupByName("default")
        try:
            base_vol = pool.storageVolLookupByName(LIBVIRT_BASE_IMAGE)
        except libvirt.libvirtError:
            pytest.skip(f"L'image de base {LIBVIRT_BASE_IMAGE} n'existe pas, test ignoré")
        
        # Créer le volume à partir de l'image de base
        volume_path = libvirt_connection.create_volume(
            volume_name, 
            volume_size, 
            base_image=LIBVIRT_BASE_IMAGE
        )
        
        # Vérifier que le volume a été créé
        assert volume_path, f"Le chemin du volume est vide: {volume_path}"
        
        # Vérifier que le volume existe en essayant de le récupérer
        volume = pool.storageVolLookupByName(volume_name)
        assert volume is not None
    
    finally:
        # Nettoyer: supprimer le volume
        try:
            pool = libvirt_connection.conn.storagePoolLookupByName("default")
            volume = pool.storageVolLookupByName(volume_name)
            volume.delete(0)
        except (libvirt.libvirtError, UnboundLocalError):
            pass  # Le volume n'existe peut-être pas, ignorer l'erreur

def test_create_and_delete_vm(libvirt_connection, test_node_config, mock_cloud_init_iso):
    """Tester la création et la suppression d'une VM"""
    # La création d'une VM est une opération longue et nécessite une configuration valide
    # on va la simuler partiellement pour éviter de créer une vraie VM
    
    try:
        # Vérifier que le réseau de test existe
        networks = libvirt_connection.conn.listAllNetworks()
        network_names = [net.name() for net in networks]
        if LIBVIRT_TEST_NETWORK not in network_names:
            pytest.skip(f"Le réseau de test {LIBVIRT_TEST_NETWORK} n'existe pas, test ignoré")
        
        # Créer un volume pour notre VM (simuler ce que create_vm ferait)
        volume_name = f"{test_node_config.name}_disk"
        volume_path = libvirt_connection.create_volume(
            volume_name, 
            test_node_config.disk_size_gb
        )
        
        # Pour tester delete_vm, nous allons créer une VM simple
        # mais sans la démarrer réellement pour éviter de consommer des ressources
        
        # Créer un XML minimal pour définir la VM
        vm_xml = f"""
        <domain type='kvm'>
            <name>{test_node_config.name}</name>
            <memory unit='MiB'>1024</memory>
            <vcpu>1</vcpu>
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
                    <source network='{test_node_config.network.name}'/>
                    <model type='virtio'/>
                </interface>
            </devices>
        </domain>
        """
        
        # Définir la VM (sans la démarrer)
        domain = libvirt_connection.conn.defineXML(vm_xml)
        assert domain is not None
        assert domain.name() == test_node_config.name
        
        # Tester vm_exists pour vérifier que la VM a été créée
        assert libvirt_connection.vm_exists(test_node_config.name) is True
        
        # Tester delete_vm
        assert libvirt_connection.delete_vm(test_node_config.name, delete_storage=True) is True
        
        # Vérifier que la VM a été supprimée
        assert libvirt_connection.vm_exists(test_node_config.name) is False
        
        # Vérifier que le volume a été supprimé
        try:
            pool = libvirt_connection.conn.storagePoolLookupByName("default")
            pool.storageVolLookupByName(volume_name)
            pytest.fail(f"Le volume {volume_name} n'a pas été supprimé correctement")
        except libvirt.libvirtError:
            # C'est normal, le volume devrait avoir été supprimé
            pass
            
    except Exception as e:
        # Nettoyage en cas d'échec du test
        try:
            if libvirt_connection.vm_exists(test_node_config.name):
                libvirt_connection.delete_vm(test_node_config.name, delete_storage=True)
        except:
            pass
        
        # Remonter l'exception pour faire échouer le test
        raise e

def test_context_manager(unique_name):
    """Tester le fonctionnement du gestionnaire de contexte (with)"""
    # Créer une connexion libvirt en utilisant with
    with LibvirtConnection(LIBVIRT_HOST, LIBVIRT_USER, LIBVIRT_IDENTITY) as conn:
        # Vérifier que la connexion est établie
        assert conn.conn is not None
        hostname = conn.conn.getHostname()
        assert hostname
    
    # Vérifier que la connexion est fermée après la sortie du bloc with
    assert conn.conn is None