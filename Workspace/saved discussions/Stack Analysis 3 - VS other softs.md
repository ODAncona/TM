
# Un provisioning sur-mesure plutôt qu’un outil standard

Dans notre cas, l’objectif est de déployer **un cluster virtuel reproductible** pour tester différents ordonnanceurs avec une topologie identique. L’environnement cible est un serveur KVM/libvirt (« rhodey ») restreint (pas de sudo). Pour répondre à ces contraintes, nous avons choisi une solution **sur-mesure** basée sur Hydra (gestion unifiée des configs), NixOS (machines pures et déclaratives) et un script Python pilotant libvirt. Cette approche n’est pas un caprice, mais la réponse aux limites des outils classiques dans ce contexte.

## Pourquoi Terraform, Ansible ou Vagrant ne conviennent pas

- **Terraform (libvirt)** : son _provider_ libvirt n’est pas toujours fiable sur un serveur restreint. Il exige souvent des ajustements système (désactiver AppArmor, modifier _security_driver_, etc.) pour éviter des erreurs de permission. De plus, Terraform ne gère pas nativement la notion de « cluster » KVM multi-nœuds – pas de gestion d’affinité ni de répartition automatique des VM sur les hôtes. En clair, le provider Terraform/libvirt est conçu pour des cas simples (création d’une VM locale) et pose problème en production avec des accès limités et des besoins de répartition complexes.
    
- **Ansible** : c’est avant tout un outil de _configuration management_. Il excelle pour installer et configurer des services sur des machines existantes, mais n’est pas optimisé pour la création déclarative d’infrastructure brute. De plus, Ansible se repose sur SSH et sudo sur l’hôte pour exécuter ses modules. Or sur _rhodey_ nous n’avons pas de sudo, ce qui empêche Ansible de gérer efficacement la création des VM ou des réseaux libvirt en bas niveau. En somme, Ansible seul ne permet pas de dire « create VM » facilement sans capacités élevées au niveau hôte, et il manque d’un moyen simple de décrire l’ensemble du cluster.
    
- **Vagrant** : cet outil est conçu pour les environnements de _développement local_ (généralement VirtualBox/VMware). Il permet surtout de configurer facilement des VM d’un développeur local, pas de construire en production un cluster dédié sur un serveur distant sans interface graphique. Vagrant est orienté boîte prête à l’emploi (« box ») pour du dev/test, et non pour piloter finement un hyperviseur KVM en environnement contraint.
    

## Avantages de la solution personnalisée

- **Contrôle fin et adaptabilité** : nous utilisons Python + libvirt via SSH pour piloter _rhodey_ en tant qu’utilisateur du groupe `libvirt`, sans privilèges root. Cette approche permet d’adapter finement chaque étape (création de disque, réseau, VM, etc.) aux contraintes du système. On évite les boîtes noires : chaque commande est explicitement codée, modifiable et déboguable.
    
- **Reproductibilité absolue avec NixOS** : chaque VM est définie par une configuration NixOS purement déclarative. NixOS garantit un environnement _100 % reproductible_ – « si ça marche quelque part, ça marchera n’importe où ». Les images de VM sont construites de façon déterministe, assurant que notre cluster aura toujours la même configuration logicielle et réseau.
    
- **Configuration globale cohérente avec Hydra** : le framework Python Hydra permet de composer de manière hiérarchique et centralisée tous les paramètres du cluster (nombre de nœuds, ressources, adresses IP, options des ordonnanceurs, etc.). On obtient ainsi un système « holistique » où un seul fichier (ou ensemble de fichiers Hydra) décrit l’ensemble de l’infrastructure. Cela assure transparence et traçabilité : toute modification passe par la configuration déclarative plutôt que par des scripts épars.
    
- **Approche déclarative et traçable** : en combinant Hydra et NixOS, on dispose d’un **déploiement déclaratif de bout en bout**. On décrit le « quoi » (topologie et logiciels) plutôt que le « comment » impératif. Chaque version de la config Hydra et chaque fichier NixOS versionnés servent de source de vérité. Cette traçabilité naturelle n’existe pas spontanément avec Terraform/Ansible qui séparent l’infra du contenu des VM.
    

En résumé, cette solution maison cible exactement nos besoins de cluster virtuel : un déploiement entièrement scripté, indéfiniment reproductible et ajustable. Elle nous affranchit des bogues ou incompatibilités rencontrés avec Terraform/libvirt (modifications manuelles du host) et contourne l’impossibilité d’utiliser sudo ou Vagrant sur _rhodey_.

## Points clés (bénéfices et limites)

- **Contrôle / Flexibilité** : nous pouvons implémenter tout comportement spécifique (par ex. allocation IP fixes, réseaux particuliers) au gré de nos tests. _(Limite : nécessité de coder ces fonctionnalités sur mesure.)_
    
- **Reproductibilité garantie** : NixOS assure que l’environnement logiciel et la configuration ne dérivent pas avec le temps. _(Limite : courbe d’apprentissage NixOS pour les contributeurs, moindre communauté de partage comparé aux outils mainstream.)_
    
- **Cohérence déclarative** : Hydra unifie toute la configuration, évitant les incohérences typiques des scripts multiples. On bénéficie d’une documentation vivante (la config elle-même). _(Limite : ajout de dépendance (Hydra) peu commun dans l’écosystème devops classique.)_
    
- **Adapté aux contraintes** : pas de sudo requis sur _rhodey_, on gère libvirt en mode « session » ou via SSH. _(Limite : il faut maintenir notre wrapper Python et l’intégration Nix/Hydra, alors que Terraform et consorts sont plus largement supportés par l’écosystème.)_
    
- **Réinventer la roue ?** : certes, développer son outil est plus coûteux qu’utiliser un produit existant. Le temps de développement et de maintenance en est une limite réelle. En revanche, ici il ne s’agit pas de recréer un générique mais de résoudre un besoin très spécifique (tests de clusters sur mesure) là où les « roues » standard montrent leurs limites.
    

## Conclusion

Cette solution maison n’a pas été choisie par dogmatisme, mais parce qu’elle répondait **précisément à nos besoins** : déploiement d’un cluster multi-VM sur KVM sans accès root, avec reproductibilité totale et paramétrage déclaratif. Les outils classiques (Terraform, Ansible, Vagrant) sont excellents pour leurs cas d’usage initiaux, mais peinent à cocher toutes nos cases simultanément. En somme, il ne s’agit pas de réinventer la roue pour le plaisir, mais de construire l’outil adéquat pour un contexte contraint. Nous restons conscients des inconvénients (effort de développement, maintenance, intégration) et prévoyons de documenter et modulariser notre solution pour en limiter l’impact négatif. Les bénéfices (contrôle, reproductibilité, traçabilité) justifient néanmoins ce choix sur-mesure face aux alternatives grand public.

**Sources et références :** caractéristiques de Hydra, forces de NixOS en matière de reproductibilité, limites du provider Terraform/libvirt, rôles respectifs de Terraform vs Ansible, orientation de Vagrant vers le dev local, et configuration utilisateur de libvirt sans sudo.