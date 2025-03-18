
Etat de l'art avec Slurm, faire des ressources dynamiques

Dipsy Université Technique de Münich Isaias

MPI: quand tu veux avoir une tâche qui utilise plusieurs preucess et peut être sur différent 2. C'est un runtime, et tu define des messages, opération collective pour faire un broadcast.

MPI est au dessus de PMI ou PMIX

On est combien ? dans ces combiens c'est quoi mon numéro et tu commences. Je veux parler au numéro tant et je veux ce numéro pour la synchronisation.

Je comprends la motivation.

J'aurais peur que ce soit compliqué.
J'aurais peur que ce soit pas scalable
Au niveau du temps, il n'y aurait pas le même temps que sur une vraie machine.

Il y a un controleur qui prend les décisions

et il y a slurmd sur agents
Il y a un process manager sur chaque noeud, qui est là pour spawn les process de l'app en elle même.

Il faut utiliser avec Munch

C'est quoi un passtrough

GPU est un device PCI express, tout ce qui est IO est filtré par le superviseur. A chaque fois ue la vm veut accéder au PCI, ça fait une interruption dans le kernel du host. Il va test si la VM client a le droit ou pas. C'est super couteux. 
Tu veux dire à ta VM je vais te dédier ce device pci EXPRESS ET CONFIGURER L'io mmu POUR DIRE QUE CETTE vm A LE DROIX DE PARLER AVEC CE DEVEICE LÀ. ça rapproche de natif. Le problème c'est que quand tu veux faire ça tu peux faire ça de manière statique. 1 GPU par VM. 

Separable Allocators. Mediatid passtrough. 


Problème de réseau.

2 partitions avec des petits CPUs et des gros gPUs et l'autre avec des CPUs puissant.

---

NUMA: non uniform memory access

C'est l'idée que quand on a beaucoup de coeur ils ne sont pas tous égaux à cause de la distance à la zone mémoire. Lorsquon a le chip, les architectes divisent ça en 4 parties et dans chaque partie il y a 2 contrôleurs mémoires. Il y a le cache L2 dans cette région là. il n'y a pas de ressources partagées avec les autres jobs qui sont dans une autre zone numa.

avec `numactl`, il faut que ces process tournent dans cette zone numa.

AMD Milan zone numa. numactl -h

Il faut garder une zone numa pour l'host. !! donc si on a n zones numa il faut garder une zone pour l'host.

Ceux qui sont dans le même socket communiquent mieux entre eux

Risque:
- Tâches qui utilisent pas trop le GPU ou émulent le GPU
- Alloue une tâche

40 de noeud

---

Dans un environnement HPC il y a des modules, il a besoin de libfft, libblas, il y a un truc qui charge dans le path les bonnes variables d'environnements.

Spack! Tu donnes une recette.

Prendre des benchmarks HPC tout simple.

Benchmark HPC
- HPCG
- LINpack
- GREEN 500

TOP 500 GO TO SEARCH

top500.org

---
Il y a des noeuds qui sont plus suceptibles de tomber en panne que d'autres.

Si on veut simuler une 40 de noeuds on a besoin de 40 fois la mémoire.

LIMITATION 
- puissance de calcul
- Mémoire par noeud mémoire


---

Vm avec linux KVM tu utilises une partie du kernel de l'hôte.

On s'expose à des différences minimes en répliquant tout.

ça me parle pas beaucoup de si j'avais 10 noeuds.

tout le monde veut les mêmes librairies et tout le monde veut ça et le système de fichier pète un câble.

---
