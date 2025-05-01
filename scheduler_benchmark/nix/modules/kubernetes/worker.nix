{ config, lib, pkgs, ... }:

let 
  kubeMasterFQDN = "k8s-master.local";
in

{

  # Packages
  environment.systemPackages = with pkgs; [
    kubernetes
  ];
  
  # Kubernetes Worker Node Configuration
  services.kubernetes = {
    roles = ["node"];
    masterAddress = kubeMasterFQDN;
    apiserverAddress = "https://${kubeMasterFQDN}:6443";
    easyCerts = true;
    addons.dns.enable = true;
  };

  networking.firewall.enable = true;
  networking.firewall.allowedTCPPorts = [
    22      # SSH
    10250   # Kubelet API
  ];
  networking.firewall.allowedTCPPortRanges = [
    { from = 30000; to = 32767; }  # NodePort services
  ];
}