{ config, lib, pkgs, ... }:

{

  environment.systemPackages = with pkgs; [
    kubectl
    kompose
    kubernetes
    ethtool
    containerd
    cri-tools
    conntrack-tools
  ];

  #   boot.kernel.sysctl = {
  #   "net.ipv4.ip_forward" = 1;
  #   "net.bridge.bridge-nf-call-iptables" = 1;
  #   "net.bridge.bridge-nf-call-ip6tables" = 1;
  # };
  # virtualisation.containerd = {
  #   enable = true;
  #   settings = {
  #     plugins."io.containerd.grpc.v1.cri".enable = true;
  #   };
  # };

  networking.hostName = "nixos-k8s-master";
  networking.useDHCP = true;


  services.kubernetes = {
    roles = ["master"];
    easyCerts = true;
    addons.dns.enable = true;
    kubelet.extraOpts = "--fail-swap-on=false";
  };
  services.kubernetes.masterAddress = "nixos-k8s-master";


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
  #services.kubernetes.masterAddress = "127.0.0.1";
  #services.kubernetes.masterAddress = "192.168.222.22";
  #
  # networking.interfaces.ens3.ipv4.addresses = [{
  #   address = "192.168.222.22";
  #   prefixLength = 24;
  # }];
  # networking.defaultGateway = {
  #   address = "192.168.222.1";
  #   interface = "enp1s0";
  # };
  # networking.nameservers = [ "192.168.222.1" "8.8.8.8" ];

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
