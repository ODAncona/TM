{ config, lib, pkgs, ... }:

{

  environment.systemPackages = with pkgs; [
    kubectl
    kompose
    kubernetes
  ];

  services.kubernetes = {
    roles = ["master"];
    easyCerts = true;
    addons.dns.enable = true;
    kubelet.extraOpts = "--fail-swap-on=false";
  };
  services.kubernetes.masterAddress = "192.168.222.22";
  # services.kubernetes = {
  #   apiserver.enable = true;
  #   controllerManager.enable = true;
  #   scheduler.enable = true;
  #   addonManager.enable = true;
  #   proxy.enable = true;
  #   flannel.enable = true;
  #   kubelet.enable = true;
  #   easyCerts = true;
  #   addons.dns.enable = true;
  #   kubelet.extraOpts = "--fail-swap-on=false";
  # };
  # services.kubernetes.masterAddress = "127.0.0.1";
  # #services.kubernetes.masterAddress = "192.168.222.22";
  #
  networking.useDHCP = false;
  networking.interfaces.ens3.ipv4.addresses = [{
    address = "192.168.222.22";
    prefixLength = 24;
  }];
  networking.defaultGateway = {
    address = "192.168.222.1";
    interface = "enp1s0";
  };
  networking.nameservers = [ "192.168.222.1" "8.8.8.8" ];

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
