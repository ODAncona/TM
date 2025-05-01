{ config, lib, pkgs, ... }:

let
  apiserverHost = "k8s-master";
  apiserverFQDN = "${apiserverHost}.local";
in
{

  # Packages
  environment.systemPackages = with pkgs; [
    kompose
    kubernetes
  ];

  networking.hostName = apiserverHost;
  services.kubernetes.masterAddress = apiserverHost;
  services.kubernetes.apiserverAddress = "https://${apiserverFQDN}:6443";
  networking.useDHCP = true;

  services.kubernetes = {
    roles = ["master"];
    easyCerts = true;
    addons.dns.enable = true;
    kubelet.extraOpts = "--fail-swap-on=false";
    apiserver = {
      securePort = 6443;
      extraSANs = [ apiserverFQDN ];
      advertiseAddress = apiserverFQDN;
    }
  };

  environment.sessionVariables = {
    KUBECONFIG = "/etc/kubernetes/cluster-admin.kubeconfig";
  };


  networking.firewall.enable = true;
  networking.firewall.allowedTCPPorts = [
    22      # SSH
    6443    # Kubernetes API Server
    2379    # etcd server client API
    2380    # etcd peer communication
    8888    # kube-scheduler
    10250   # Kubelet API
    10251   # kube-scheduler
    10252   # kube-controller-manager
  ];
  networking.firewall.allowedTCPPortRanges = [
    { from = 30000; to = 32767; }  # NodePort services
  ];
}
