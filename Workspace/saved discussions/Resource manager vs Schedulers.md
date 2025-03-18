**TLDR;**

Un **Resource Manager** est responsable de l'allocation des ressources physiques du cluster (CPU, GPU, mémoire, stockage) aux différents jobs.

Un **Job Scheduler** gère l'exécution des jobs sur ces ressources selon des priorités, des politiques d’allocation, et des dépendances.

---

### **1. Resource Manager : allocation et suivi des ressources**

Le **resource manager** est responsable de **suivre en temps réel** l'état des ressources du cluster (CPU, GPU, RAM, stockage, réseau) et de les **allouer** aux jobs en fonction des besoins et des politiques définies.

Fonctions typiques d'un **resource manager** :

- Connaître l'état de chaque machine (CPU utilisés, mémoire disponible, charge réseau, etc.).
- Fournir au scheduler la liste des ressources disponibles.
- Isoler les jobs dans des environnements contrôlés (cgroups, namespaces, conteneurs).
- Gérer les limites de consommation des ressources.
- Préempter ou suspendre un job si nécessaire (ex: si une tâche critique doit passer en priorité).

Exemple : **Slurm, Flux, PBSPro ont un composant resource manager**.

---

### **2. Job Scheduler : ordonnancement et exécution des jobs**

Le **job scheduler**, lui, prend les jobs soumis par les utilisateurs, applique une **politique de planification** (FIFO, priorité, fair-share, backfilling, etc.), et décide **quand et où** un job doit être exécuté.

Fonctions typiques d'un **scheduler** :

- Décider **quel job démarre en premier** selon des critères comme la priorité, la politique d’équité, etc.
- Décider **sur quelle machine un job doit s’exécuter** en fonction des ressources demandées.
- Gérer les files d'attente de jobs (jobs en attente, jobs en cours, jobs terminés).
- Adapter la planification en temps réel (backfilling pour minimiser l’attente).

Exemple : **Slurm, PBSPro, LSF, HTCondor sont aussi des job schedulers**.

---

|**Fonction**|**Resource Manager**|**Job Scheduler**|
|---|---|---|
|Suit l’état des ressources (CPU, RAM, GPU)|✅ Oui|❌ Non|
|Alloue les ressources physiques|✅ Oui|❌ Non|
|Prend des décisions de planification|❌ Non|✅ Oui|
|Gère les files d’attente de jobs|❌ Non|✅ Oui|
|Exécute un job sur une ressource allouée|✅ Oui|✅ Oui (mais indirectement)|

---

SLURM
Kubernetes + Scheduler
Ray
Run.ai
Flux

Système complet de gestion de jobs et de ressources:

Slurm, PBSPro, Flux, HTCondor

Gestion des workflows, complément aux planificateurs classiques:

**RadicalPilot, Balsam, Parsl**

