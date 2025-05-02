### Points Clés
- Il semble probable que notre choix de ne pas utiliser Terraform, Ansible ou Vagrant soit justifié par des besoins spécifiques en reproductibilité et contrôle.
- La recherche suggère que Nix et Libvirt offrent des avantages pour les environnements HPC, notamment en termes de déterminisme.
- Les preuves penchent vers une meilleure intégration avec notre infrastructure existante et une flexibilité accrue pour les configurations complexes.

### Introduction
Dans notre projet de benchmarking des ordonnanceurs HPC, nous avons opté pour une solution personnalisée utilisant Nix flakes, Hydra et un wrapper Python pour Libvirt, plutôt que des outils comme Terraform, Ansible ou Vagrant. Voici une explication claire et simple pour comprendre pourquoi.

### Pourquoi Nous N'avons Pas Utilisé Ces Outils
**Reproductibilité Essentielle**  
Pour des benchmarks scientifiques, il est crucial que les résultats soient reproductibles. Nix flakes garantissent que chaque environnement est déterministe, ce qui signifie que les mêmes entrées produisent toujours les mêmes sorties. Terraform et Ansible, bien qu'efficaces, ne garantissent pas ce niveau de reproductibilité, surtout pour les dépendances logicielles qui peuvent varier.

**Contrôle Précis de l'Environnement Logiciel**  
Nix nous permet de contrôler précisément les versions des paquets et leurs dépendances, essentiel pour comparer équitablement différents ordonnanceurs. Avec Ansible, obtenir ce niveau de précision nécessiterait plus d'efforts et pourrait être moins fiable.

**Optimisation pour le Matériel Spécifique**  
Notre projet s'exécute sur Rhodey, un serveur avec une topologie CPU spécifique. Une solution personnalisée avec Libvirt nous permet d'optimiser les clusters virtuels pour exploiter au mieux ce matériel, contrairement à Vagrant, qui pourrait manquer de flexibilité pour ces besoins HPC.

**Intégration et Expertise Existante**  
Notre équipe est déjà familière avec Nix et Libvirt, et Hydra s'intègre bien à nos flux de travail actuels. Adopter Terraform ou Ansible aurait demandé un apprentissage supplémentaire et risqué de perturber nos processus.

**Flexibilité pour l'Avenir**  
Notre système personnalisé est conçu pour s'adapter facilement à des extensions futures, comme des clusters plus grands ou de nouveaux types de charges de travail, offrant une flexibilité que des outils génériques pourraient ne pas supporter aussi bien.

---

### Note Détaillée
Dans le cadre de notre projet de benchmarking des ordonnanceurs HPC, visant à comparer SLURM, Kubernetes+Volcano et Flux Framework en termes d'utilisation des ressources, d'équité, de temps de complétion des tâches et d'élasticité, nous avons choisi de développer une solution personnalisée plutôt que d'utiliser des outils comme Terraform, Ansible ou Vagrant. Cette décision, bien que contre-intuitive pour certains, repose sur des considérations techniques et opérationnelles spécifiques, détaillées ci-dessous.

#### Contexte du Projet
Le projet, intitulé "Benchmark Specification: Multi-Objective Comparison of HPC Schedulers", cherche à évaluer les performances de différents ordonnanceurs sur des clusters virtuels variés, avec des charges de travail comme HPL et HPCG. Les expériences sont exécutées sur Rhodey, un serveur du Lawrence Berkeley National Laboratory, et orchestrées depuis un laptop X1-Carbon sous Arch Linux. L'architecture expérimentale repose sur une séparation entre configuration statique (OS, logiciels) et dynamique (provisionnement des VM, déploiement des applications), avec un accent sur la reproductibilité, la flexibilité et l'automatisation.

#### Analyse des Outils Alternatifs
Avant d'expliquer notre choix, examinons brièvement les outils mentionnés :
- **Terraform** : Outil de code d'infrastructure déclaratif, principalement utilisé pour gérer des ressources cloud. Il permet de définir et provisionner des infrastructures, mais son focus est souvent sur des environnements cloud plutôt que sur des VM locales pour HPC.
- **Ansible** : Outil d'automatisation pour la gestion de configuration, le déploiement d'applications et l'automatisation des tâches, utilisant des fichiers YAML pour décrire l'état souhaité. Il est largement utilisé dans l'HPC pour la gestion de configuration, mais peut nécessiter des scripts extensifs pour des setups complexes.
- **Vagrant** : Outil pour construire et gérer des environnements de machines virtuelles, idéal pour le développement, mais potentiellement limité pour des clusters HPC à grande échelle ou des configurations spécifiques.

#### Justification de Notre Approche
Notre méthodologie repose sur plusieurs piliers, chacun justifiant notre choix de ne pas utiliser ces outils :

1. **Reproductibilité et Déterminisme**  
   La reproductibilité est au cœur de notre projet, car des résultats cohérents sont essentiels pour des comparaisons scientifiques valides. Nix flakes, que nous utilisons, garantissent des builds déterministes, où les mêmes entrées produisent toujours les mêmes sorties. Cela est crucial pour assurer que les benchmarks, exécutés sur des clusters virtuels avec des configurations variées, restent comparables.  
   En comparaison, Terraform et Ansible, bien qu'efficaces pour gérer des infrastructures, ne garantissent pas le même niveau de reproductibilité pour la pile logicielle. Par exemple, les versions des paquets peuvent changer au fil du temps, introduisant des variations non désirées. Nix, avec son approche fonctionnelle, élimine ces risques en gérant les dépendances de manière isolée et reproductible.

2. **Contrôle Précis de l'Environnement Logiciel**  
   Pour évaluer des métriques comme l'utilisation des ressources (\(\alpha\)), l'équité (\(\beta\)), le temps de complétion des tâches (\(\gamma\)) et l'élasticité (\(\delta\)), il est impératif que l'environnement logiciel soit identique à chaque exécution. Nix nous permet de définir exactement les versions des paquets et leurs dépendances, assurant des conditions de test uniformes.  
   Avec Ansible, bien que possible, obtenir ce niveau de précision nécessiterait des playbooks complexes et des efforts supplémentaires pour piner les versions, ce qui pourrait introduire des erreurs ou réduire la maintenabilité. Nix, grâce à son modèle de gestion des paquets, simplifie cette tâche et garantit une cohérence à travers les expérimentations.

3. **Optimisation pour le Matériel Spécifique**  
   Nos benchmarks s'exécutent sur Rhodey, un serveur mimant la topologie CPU d'un nœud Perlmutter, avec 2x AMD EPYC 7763, 512 Go de mémoire DDR4, et une connexion PCIe 4.0. Pour exploiter pleinement ces capacités, notamment les domaines NUMA et les interconnexions haute performance, une solution personnalisée s'impose.  
   Nous utilisons un wrapper Python basé sur Libvirt pour provisionner et configurer les VM, permettant une gestion fine des ressources (CPU, RAM, disque, réseau) adaptée à ces spécificités. Vagrant, bien qu'utile pour des environnements de développement, pourrait manquer de flexibilité pour ces optimisations HPC, et son support pour des configurations avancées comme les interconnexions pourrait être limité.

4. **Intégration avec les Outils et l'Expertise Existants**  
   Notre équipe dispose d'une expertise significative avec Nix, Hydra et Libvirt, outils déjà intégrés dans nos flux de travail. Hydra gère les configurations hiérarchiques complexes, essentielles pour définir l'espace d'entrée (\(A, B, C\)), incluant les topologies de cluster, les configurations des nœuds et les paramètres des ordonnanceurs.  
   Adopter Terraform ou Ansible aurait nécessité un apprentissage supplémentaire et risqué de perturber nos processus existants. De plus, notre système actuel, avec Nix flakes pour les images de base et Hydra pour les configurations, s'intègre seamlessement avec notre pipeline, facilitant la maintenance et l'évolution.

5. **Flexibilité et Extensibilité**  
   Notre système de provisionnement est conçu pour s'adapter à des extensions futures, comme des clusters plus grands, des ordonnanceurs supplémentaires ou de nouveaux types de charges de travail (par exemple, des workloads au-delà de HPL et HPCG). Cela est crucial pour notre recherche, qui explore l'espace de Pareto des métriques \(O = \{\alpha, \beta, \gamma, \delta\}\) et identifie des compromis optimaux.  
   Terraform, Ansible et Vagrant, bien qu'évolutifs, pourraient imposer des limitations dans des scénarios complexes, notamment pour des configurations dynamiques post-provisionnement, comme les adresses IP et les noms d'hôte dépendants de la configuration, gérés automatiquement dans notre approche.

#### Comparaison Résumée
Pour illustrer, voici un tableau comparatif des outils, basé sur nos besoins spécifiques :

| **Critère**               | **Nix + Hydra + Libvirt** | **Terraform** | **Ansible** | **Vagrant** |
|---------------------------|---------------------------|---------------|-------------|-------------|
| Reproductibilité          | Excellent (déterministe)  | Modéré        | Modéré      | Modéré      |
| Contrôle logiciel         | Très précis               | Limité        | Possible, effort requis | Limité      |
| Optimisation HPC          | Hautement personnalisable | Faible        | Modéré      | Faible      |
| Intégration existante     | Fortement intégré         | Nécessite adaptation | Nécessite adaptation | Nécessite adaptation |
| Flexibilité future        | Très flexible             | Modéré        | Modéré      | Limité      |

#### Conclusion
En résumé, notre choix de ne pas utiliser Terraform, Ansible ou Vagrant repose sur des besoins spécifiques en reproductibilité, contrôle précis, optimisation pour le matériel HPC, intégration avec nos outils existants et flexibilité pour des extensions futures. Bien que ces outils soient puissants dans d'autres contextes, notre solution personnalisée, centrée sur Nix, Hydra et Libvirt, répond mieux aux exigences de notre projet de recherche, garantissant des résultats fiables et des capacités d'évolution pour des études futures.

---

### Citations Clés
- [NixOS: A Declarative Approach to Configuration Management](https://nixos.org/)
- [Hydra: A Continuous Build System for Nix](https://nixos.org/hydra/)
- [Libvirt: The Virtualization API](https://libvirt.org/)