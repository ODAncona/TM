 disaggregated computing Sur mesure dans conception d'ordinateurs. Chiplet, HW, casser des bouts de puces rack de ram, rack de CPU et les connecter à la demande. Ils ont réussi à faire ça avec de la virtualisation (container, Kubernetes) HPL => High performance linepack (stress CPU) HPCG => conjugate gradient (stress mémoire, réseau) Graph 500 => stress réseau AI top 500 => stress opération 8 bits Linear algebra right now the problem storming in office => i need gpu asap right here right now exclusive private access to gpu and ressource steering (concept développé par eux) avec le steering on navigue dans quel sens on va metre les ressources patch pannel, qqn va le recâbler => litéralement mettre un rj45 entre bureau introduire système de sharing//pooling avec une queue. what are different system to share/pool ? software stack ? Ils veulent installer SLURM à la HEIA. Il faut décrire l'env.  Augmenter l'utilisation des GPUs. Ils partent du HW => et ils vont l'allouer à des user. Dans quelle direction ça va leur rendre service dans le cas de la virtualisation. Comparaison de Scheduler Comparer contre SLURM Inclure un aspect lié au chiplet lbnl => fonctionnaires fédéraux département énergie DOE UB => état de californie But Faire une publication. # HPC: informatique soit une machine est insuffisante pour traiter le pb car elle a pas les ressources OU on a besoin d'accélérer les calculs substantiellements. TTS time to solution File d'attente Datacenter High Throughput Temps global doit être inférieur au temps d'attente. besoin, c'est d'avoir un calcul qui se fasse rapidement. Scheduling doit trouver des affinités entre les jobs avec la diversité de Kubernetes réduit les coûts opérationnels. Lorsque le problème est énorme, comment mapper un problème qui ne tient pas sur une tranche de pain. Vrai calcul parallel avec MPI. pleins de problèmes sur 1 hardware. 5-6 Décembre 17h # Présentation: Présentation Skills Faire un résumé de NTDE Base de ce qu'il m'a donné sur le besoin pratique HEIA Question de benchmarking Montrer qu'on a une architecture hétérogène. Trouver next step. Mapper un problème informatique sur des ressources. RAM + CPU + GPU + NEtwork (Scheduling)

---

Bill d'Ali.

Sur dimensionné sur certains aspects et sous-dimensionner pour des autres. 

right now the problem storming in office => i need gpu asap right here right now exclusive private access to gpu 

nersk => Computing center

But Faire une publication. 

throughout: Spark, Kafka 

#### 1. **What the Computer Architecture Group at Berkeley Does**
   - **Disaggregated Computing**: 
     - Concept of building custom computers by assembling chiplets (CPU, RAM, etc.) and connecting them as needed.
     - On-demand hardware composition, e.g., racks of RAM and CPU.
   - **Resource Steering**:
     - Dynamically allocates resources (e.g., GPUs) based on demand.
     - Users can steer the allocation process to get exclusive access.
   - **Virtualization**:
     - Containers (Kubernetes) for efficient use of resources.
     - Reduces operational costs and increases resource utilization.

#### 2. **Notes on HPC**
   - **Key Benchmarks**:
     - **HPL (High Performance Linpack)**: CPU stress.
     - **HPCG (High Performance Conjugate Gradient)**: Memory and network stress.
     - **Graph 500**: Network stress.
     - **AI Top 500**: 8-bit operations stress.
   - **Resource Allocation Issues**:
     - Current demand: Immediate, exclusive GPU access.
     - Physical patch panel analogy: manually connect cables (e.g., RJ45) to allocate resources.
     - Concept of job queuing and resource pooling to enhance GPU utilization.
   - **Scheduler Comparison**:
     - SLURM (to be installed at HEIA) vs other schedulers.
     - How virtualization (Kubernetes) impacts resource allocation efficiency.
   - **Key Metrics**:
     - **TTS (Time to Solution)**: Minimize global computation time.
     - **Throughput**: Improve data center efficiency.
   - **Parallel Computing**:
     - Challenges in mapping large problems to hardware.
     - Use of MPI for real parallel computation.
     - Tools: Spark, Kafka for data throughput.

#### 3. **Presentation Structure**
   - **Introduction**: 
     - Who you are: Academic Background ( DataScience, work at institut d'automatisation industriel, aime l'optimisation, dernière année à faire du MLOPS)
     - Présenter NTDE Paper
     - Présenter AiMarket + MachleData
     - Urge: Develop framework // to optimize AI computation for a compagny
   - **Goals for Collaboration**:
	   - Want to do dynamic Benchmarking job more heavy on (ram, cpu, network)
	   - Want to define reasoning framework to adapt infrastructure to any need (heterogenous architecture)
	   - Need strong benchmarking experience (LBNL)
	   - Need strong resources allocation experience (LBNL)
	   - Present HEIA’s HPC setup and the plan to enhance it (more throughput)
   - **Proposed Framework**:
     - Collaboration goals.
     - Kubernetes Scheduler comparison (paretto frontier)
     - Next steps: Implementing and testing SLURM.
     - Resource mapping for optimized scheduling.
   - **Conclusion**:
     - Highlight potential outcomes.
     - Questions and feedback session.

Let me know if you'd like any refinements or additions.