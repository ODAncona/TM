## Types de benchmarks

### Micro Benchmarks

Ce sont les benchmarks de plus bas niveau qui testent une seule opération à la fois2 . Ils ne cherchent pas à faire plus qu'une seule opération. Par exemple, ils peuvent tester la communication entre deux nœuds ou un collectif entre plusieurs nœuds. La métrique rapportée peut être la bande passante ou le temps d'achèvement (parfois appelé latence)2 . La fonctionnalité principale couverte par ce type de benchmark est la couche MPI, y compris les algorithmes collectifs et leur sélection automatique, ainsi que l'API entre la librairie MPI et le logiciel et le firmware du fournisseur (comme OFA verbs, OFI ou UCX). Ils testent également le logiciel et le matériel du fournisseur, comme dans le cas de Rocky et RDMA, ainsi que les éléments de réseau et le contrôle de la congestion et leur interaction2 . Des exemples de micro benchmarks incluent Linux RDMA perf test, OSU Benchmark, Intel MPI Benchmark, ainsi que Nickel et Recall test4 . Ces derniers utilisent la librairie MPI ou une librairie de communication (comme Nickel) pour effectuer des opérations plus avancées que la simple communication point-à-point, incluant des collectifs comme allreduce et all to all, ainsi que la diffusion (broadcast)4 .

### Application benchmarks

Ce sont des codes complets visant à effectuer une simulation, un entraînement ML ou tout autre type de calcul distribué2 . Dans ce type de benchmarks, il y a à la fois du calcul et de la communication avec divers motifs d'interaction2 . Les métriques sont généralement le temps d'achèvement et le passage à l'échelle (scaling) de la performance de l'application avec le nombre de nœuds et de processus par nœud2 . Les composants évalués sont beaucoup plus larges, incluant tout ce qui est mentionné pour les micro benchmarks, mais aussi les CPUs, GPUs, la mémoire, les E/S, le système d'exploitation, etc.2 . Ces benchmarks donnent une bonne indication de la performance globale du système pour les utilisateurs qui souhaitent exécuter ce type d'application2 . Des exemples dans le domaine du HPC incluent les applications de prévision météorologique et les applications de dynamique moléculaire comme Gromacs et Lamps5 .... Dans le domaine du Machine Learning, on peut utiliser des modèles de réseaux neuronaux open source et les exécuter avec des frameworks comme PyTorch ou TensorFlow7 ....

### Intermediate level benchmarks

Ces benchmarks se situent entre les micro benchmarks de bas niveau et les benchmarks d'application3 . Ils tentent d'être plus génériques tout en se concentrant sur un certain type de communication3 . Ils peuvent combiner plusieurs types de calculs avec la communication nécessaire3 . Des exemples incluent HPL, HPCG et HPCC3 .... HPL se concentre sur la factorisation et la résolution de systèmes d'équations linéaires, impliquant principalement des multiplications matricielles5 . HPCG complète HPL en utilisant le gradient conjugué, qui implique des accès aux données plus irréguliers et des collectifs de voisinage5 . HPCC est un ensemble de sept tests qui se concentrent sur différents aspects du système, dont la communication5 . GPC net est un autre benchmark de ce niveau, axé sur l'évaluation de l'efficacité du réseau et du contrôle de la congestion en mesurant l'impact du réseau sous charge3 . Il mesure la performance d'opérations sous charge par rapport à leur performance sans charge3 .

---

## Exemples de benchmarks

### Micro Benchmarks:

- Linux RDMA perf test : Il s'agit d'un petit ensemble de tests qui évaluent la communication point-à-point entre deux nœuds en utilisant l'interface native verbs sans passer par la librairie MPI. Il teste les opérations RDMA de base.
- OSU Benchmark : Il utilise la librairie MPI pour réaliser des opérations plus avancées que la simple communication point-à-point, incluant des collectifs comme allreduce, all to all et la diffusion (broadcast).
- Intel MPI Benchmark : Similaire à OSU Benchmark, il utilise la librairie MPI pour tester diverses opérations de communication, y compris les collectifs.
- Nickel test : Il utilise une librairie de communication (Nickel) pour effectuer des opérations plus avancées que la simple communication point-à-point, incluant des collectifs.
- Recall test : Similaire à Nickel, il utilise une librairie de communication pour tester des opérations de communication, y compris les collectifs.

### Benchmarks d'application:

- Applications HPC:
	- Applications de prévision météorologique : Elles simulent une zone géographique divisée en sous-zones où chaque processus MPI effectue des calculs et échange des données aux frontières avec ses voisins à chaque itération.
	- Applications de dynamique moléculaire (exemples : Gromacs, Lamps) : Elles simulent le comportement de molécules en divisant le système en sous-volumes et en échangeant des paramètres entre les voisins à chaque itération. Lamps peut simuler des écoulements de fluides et d'autres phénomènes.
	- D'autres applications HPC comme celles de dynamique des fluides, d'acoustique et d'optique peuvent également servir de benchmarks. Elles partagent la caractéristique de diviser le problème en sous-volumes ou sous-zones avec des échanges de paramètres entre voisins à chaque itération.
- Applications de Machine Learning:
	- Utilisation de modèles de réseaux neuronaux open source (exemples : ResNet 50 pour la classification d'images, SSD pour la détection d'objets, DLRM pour les systèmes de recommandation) exécutés avec des frameworks comme PyTorch ou TensorFlow et des jeux de données publics.

### Benchmarks de niveau intermédiaire

- HPL (High-Performance Linpack) : Il se concentre sur la factorisation et la résolution de systèmes d'équations linéaires, impliquant principalement des multiplications matricielles.
- HPCG (High-Performance Conjugate Gradients) : Il complète HPL en utilisant la méthode du gradient conjugué, impliquant des accès aux données plus irréguliers et des collectifs de voisinage.
- HPCC (High-Performance Computing Challenge) : Il s'agit d'une suite de sept tests qui se concentrent sur différents aspects du système, y compris la communication, la mémoire et les opérations en virgule flottante.
- GPC net : Il est axé sur l'évaluation de l'efficacité du réseau et du contrôle de la congestion en mesurant l'impact du réseau sous charge sur la performance d'opérations MPI. Il compare la performance d'opérations avec et sans charge réseau significative