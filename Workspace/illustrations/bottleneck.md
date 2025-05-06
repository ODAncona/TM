
@startuml
title Current Workflow and Bottlenecks

actor Developer as dev

box "X1-Carbon Laptop (Orchestration)" #LightBlue
  participant "Nix Image Build\n(~3 min)" as build
  database "Local VM Image\n(~3.3 GB)" as local_img
  participant "Python Provisioning Script\n(Libvirt wrapper)" as prov_script
end box


box "Rhodey Server (Remote Compute)" #LightGreen
  database "VM Image Storage" as remote_img
  participant "Libvirt Hypervisor" as libvirt
  participant "Virtual Machines" as vms
  participant "Kubernetes Cluster" as k8s
end box

dev -> build : Trigger Image Build
build -> local_img : Generate Image (~3.3 GB)
local_img -> wifi : Upload Image (~4 min)
wifi -> remote_img : Store Image on Rhodey
dev -> prov_script : Launch Provisioning Script
prov_script --> libvirt : SSH Connection
libvirt -> remote_img : Use Uploaded Image
libvirt -> vms : Create VMs from Image

note over wifi : Bottleneck:\nSlow upload (3.3GB @ 15MB/s ≈ 4 min per iteration)
@enduml