{ config, lib, pkgs, ... }:

{
  services.kubernetes = {
    roles = ["master"];
    easyCerts = true;
    addons.dns.enable = true;
    kubelet.extraOpts = "--fail-swap-on=false";
  };
  services.kubernetes.masterAddress = "192.168.222.22";

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