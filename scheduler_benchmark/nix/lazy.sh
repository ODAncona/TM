#!/usr/bin/env bash
set -e  # Exit on error

# Configurations
REMOTE_USER="odancona"
REMOTE_HOST="rhodey"
REMOTE_DIR="/home/odancona/.local/share/libvirt/images/"
IMAGES=("k8s-worker" "k8s-master")

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}Début du processus de build et déploiement des images Kubernetes${NC}"

for IMAGE in "${IMAGES[@]}"; do
    echo -e "${YELLOW}Construction de l'image ${IMAGE}...${NC}"
    
    # Construction de l'image
    nix build ".#${IMAGE}" --impure
    
    # Renommage et copie de l'image
    IMG_NAME="nixos-${IMAGE}.img"
    cp "result/nixos.qcow2" "${IMG_NAME}"
    
    # Suppression de l'image distante si elle existe
    REMOTE_IMG_PATH="${REMOTE_DIR}${IMG_NAME}"
    echo -e "${BLUE}Vérification de l'existence de ${IMG_NAME} sur ${REMOTE_HOST}...${NC}"
    
    if ssh "${REMOTE_USER}@${REMOTE_HOST}" "test -f ${REMOTE_IMG_PATH}"; then
        echo -e "${YELLOW}Suppression de l'image existante sur ${REMOTE_HOST}...${NC}"
        ssh "${REMOTE_USER}@${REMOTE_HOST}" "rm ${REMOTE_IMG_PATH}"
    fi
    
    echo -e "${YELLOW}Transfert de l'image ${IMG_NAME} vers ${REMOTE_HOST}...${NC}"
    
    # Copie vers le serveur distant
    scp "${IMG_NAME}" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}"
    
    echo -e "${GREEN}Image ${IMG_NAME} déployée avec succès sur ${REMOTE_HOST}${NC}"
    
    # Nettoyage local
    rm -f "${IMG_NAME}"
done

echo -e "${GREEN}Toutes les images ont été construites et déployées avec succès!${NC}"