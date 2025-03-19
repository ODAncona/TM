@startuml
skinparam componentStyle rectangle
skinparam backgroundColor transparent
skinparam linetype ortho

package "Nœud Rhodey CPU (128 cœurs, 2TB RAM)" {
  
  package "Host"{
component "Orchestration (Terraform + Ansible + Python/Hydra)" as Orchestration
  component "Métriques & Analyse (Prometheus, Grafana, MLflow, Jupyter)" as Metrics

}
  
package "Clusters" {
  component "SLURM Cluster" as SLURM {
    component "VM 1" as VM1_1
    component "VM 2" as VM1_2
  }
  
  component "Kubernetes Cluster" as K8s {
    component "VM 1" as VM2_1
    component "VM 2" as VM2_2
  }
  
  component "Flux Cluster" as Flux {
    component "VM 1" as VM3_1
    component "VM 2" as VM3_2
  }
  
}
  Host -[hidden]d-> Clusters
}
@enduml