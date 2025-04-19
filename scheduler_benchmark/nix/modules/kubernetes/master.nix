{ config, lib, pkgs, masterIP ? "192.168.222.122", ... }:

{
  services.kubernetes = {
    roles = ["master"];
    masterAddress = masterIP;
    apiserverAddress = masterIP;
    easyCerts = true;
  };

  networking.firewall.enable = true;
  networking.firewall.allowedTCPPorts = [
    22      # SSH
    6443    # Kubernetes API Server
    2379    # etcd server client API
    2380    # etcd peer communication
    10250   # Kubelet API
    10251   # kube-scheduler
    10252   # kube-controller-manager
  ];
  networking.firewall.allowedTCPPortRanges = [
    { from = 30000; to = 32767; }  # NodePort services
  ];
}