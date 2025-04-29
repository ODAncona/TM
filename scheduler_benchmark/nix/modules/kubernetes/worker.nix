{ config, lib, pkgs, masterIP ? "192.168.222.22", ... }:

{

  environment.systemPackages = with pkgs; [
    kubectl
  ];

  # Kubernetes Worker Node Configuration
  # services.kubernetes = {
  #   kubelet.enable = true;
  #   proxy.enable = true;
  #   flannel.enable = true;
  #   easyCerts = true;
  # };

  networking.useDHCP = true;

  # Kubernetes Worker Node Configuration
  services.kubernetes = {
    roles = ["node"];
    masterAddress = masterIP; # dynamically provided
    apiserverAddress = masterIP; # dynamically provided
    easyCerts = true;
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
