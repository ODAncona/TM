Je veux utiliser créer 2 images pour créer un cluster k8s manuellement avec nixos.

Doc
===
Kubernetes
The NixOS Kubernetes module is a collective term for a handful of individual submodules implementing the Kubernetes cluster components.

There are generally two ways of enabling Kubernetes on NixOS. One way is to enable and configure cluster components appropriately by hand:

services.kubernetes = {
  apiserver.enable = true;
  controllerManager.enable = true;
  scheduler.enable = true;
  addonManager.enable = true;
  proxy.enable = true;
  flannel.enable = true;
};
Another way is to assign cluster roles (“master” and/or “node”) to the host. This enables apiserver, controllerManager, scheduler, addonManager, kube-proxy and etcd:

services.kubernetes.roles  = [ "master" ];
While this will enable the kubelet and kube-proxy only:

services.kubernetes.roles  = [ "node" ];
Assigning both the master and node roles is usable if you want a single node Kubernetes cluster for dev or testing purposes:

services.kubernetes.roles  = [ "master" "node" ];
Note: Assigning either role will also default both services.kubernetes.flannel.enable and services.kubernetes.easyCerts to true. This sets up flannel as CNI and activates automatic PKI bootstrapping.

As of kubernetes 1.10.X it has been deprecated to open non-tls-enabled ports on kubernetes components. Thus, from NixOS 19.03 all plain HTTP ports have been disabled by default. While opening insecure ports is still possible, it is recommended not to bind these to other interfaces than loopback. To re-enable the insecure port on the apiserver, see options: services.kubernetes.apiserver.insecurePort and services.kubernetes.apiserver.insecureBindAddress

Note
As of NixOS 19.03, it is mandatory to configure: services.kubernetes.masterAddress. The masterAddress must be resolveable and routeable by all cluster nodes. In single node clusters, this can be set to localhost.

Role-based access control (RBAC) authorization mode is enabled by default. This means that anonymous requests to the apiserver secure port will expectedly cause a permission denied error. All cluster components must therefore be configured with x509 certificates for two-way tls communication. The x509 certificate subject section determines the roles and permissions granted by the apiserver to perform clusterwide or namespaced operations. See also: Using RBAC Authorization.

The NixOS kubernetes module provides an option for automatic certificate bootstrapping and configuration, services.kubernetes.easyCerts. The PKI bootstrapping process involves setting up a certificate authority (CA) daemon (cfssl) on the kubernetes master node. cfssl generates a CA-cert for the cluster, and uses the CA-cert for signing subordinate certs issued to each of the cluster components. Subsequently, the certmgr daemon monitors active certificates and renews them when needed. For single node Kubernetes clusters, setting services.kubernetes.easyCerts = true is sufficient and no further action is required. For joining extra node machines to an existing cluster on the other hand, establishing initial trust is mandatory.

To add new nodes to the cluster: On any (non-master) cluster node where services.kubernetes.easyCerts is enabled, the helper script nixos-kubernetes-node-join is available on PATH. Given a token on stdin, it will copy the token to the kubernetes secrets directory and restart the certmgr service. As requested certificates are issued, the script will restart kubernetes cluster components as needed for them to pick up new keypairs.

Note
Multi-master (HA) clusters are not supported by the easyCerts module.

In order to interact with an RBAC-enabled cluster as an administrator, one needs to have cluster-admin privileges. By default, when easyCerts is enabled, a cluster-admin kubeconfig file is generated and linked into /etc/kubernetes/cluster-admin.kubeconfig as determined by services.kubernetes.pki.etcClusterAdminKubeconfig. export KUBECONFIG=/etc/kubernetes/cluster-admin.kubeconfig will make kubectl use this kubeconfig to access and authenticate the cluster. The cluster-admin kubeconfig references an auto-generated keypair owned by root. Thus, only root on the kubernetes master may obtain cluster-admin rights by means of this file.
===

module nix
===
Project Path: kubernetes

Source Tree:

```txt
kubernetes
├── addon-manager.nix
├── addons
│   └── dns.nix
├── apiserver.nix
├── controller-manager.nix
├── default.nix
├── flannel.nix
├── kubelet.nix
├── pki.nix
├── proxy.nix
└── scheduler.nix

```

`kubernetes/addon-manager.nix`:

```nix
{
  config,
  lib,
  pkgs,
  ...
}:
let
  top = config.services.kubernetes;
  cfg = top.addonManager;

  isRBACEnabled = lib.elem "RBAC" top.apiserver.authorizationMode;

  addons = pkgs.runCommand "kubernetes-addons" { } ''
    mkdir -p $out
    # since we are mounting the addons to the addon manager, they need to be copied
    ${lib.concatMapStringsSep ";" (a: "cp -v ${a}/* $out/") (
      lib.mapAttrsToList (name: addon: pkgs.writeTextDir "${name}.json" (builtins.toJSON addon)) (
        cfg.addons
      )
    )}
  '';
in
{
  ###### interface
  options.services.kubernetes.addonManager = with lib.types; {

    bootstrapAddons = lib.mkOption {
      description = ''
        Bootstrap addons are like regular addons, but they are applied with cluster-admin rights.
        They are applied at addon-manager startup only.
      '';
      default = { };
      type = attrsOf attrs;
      example = lib.literalExpression ''
        {
          "my-service" = {
            "apiVersion" = "v1";
            "kind" = "Service";
            "metadata" = {
              "name" = "my-service";
              "namespace" = "default";
            };
            "spec" = { ... };
          };
        }
      '';
    };

    addons = lib.mkOption {
      description = "Kubernetes addons (any kind of Kubernetes resource can be an addon).";
      default = { };
      type = attrsOf (either attrs (listOf attrs));
      example = lib.literalExpression ''
        {
          "my-service" = {
            "apiVersion" = "v1";
            "kind" = "Service";
            "metadata" = {
              "name" = "my-service";
              "namespace" = "default";
            };
            "spec" = { ... };
          };
        }
        // import <nixpkgs/nixos/modules/services/cluster/kubernetes/dns.nix> { cfg = config.services.kubernetes; };
      '';
    };

    enable = lib.mkEnableOption "Kubernetes addon manager";
  };

  ###### implementation
  config = lib.mkIf cfg.enable {
    environment.etc."kubernetes/addons".source = "${addons}/";

    systemd.services.kube-addon-manager = {
      description = "Kubernetes addon manager";
      wantedBy = [ "kubernetes.target" ];
      after = [ "kube-apiserver.service" ];
      environment.ADDON_PATH = "/etc/kubernetes/addons/";
      path = [ pkgs.gawk ];
      serviceConfig = {
        Slice = "kubernetes.slice";
        ExecStart = "${top.package}/bin/kube-addons";
        WorkingDirectory = top.dataDir;
        User = "kubernetes";
        Group = "kubernetes";
        Restart = "on-failure";
        RestartSec = 10;
      };
      unitConfig = {
        StartLimitIntervalSec = 0;
      };
    };

    services.kubernetes.addonManager.bootstrapAddons = lib.mkIf isRBACEnabled (
      let
        name = "system:kube-addon-manager";
        namespace = "kube-system";
      in
      {

        kube-addon-manager-r = {
          apiVersion = "rbac.authorization.k8s.io/v1";
          kind = "Role";
          metadata = {
            inherit name namespace;
          };
          rules = [
            {
              apiGroups = [ "*" ];
              resources = [ "*" ];
              verbs = [ "*" ];
            }
          ];
        };

        kube-addon-manager-rb = {
          apiVersion = "rbac.authorization.k8s.io/v1";
          kind = "RoleBinding";
          metadata = {
            inherit name namespace;
          };
          roleRef = {
            apiGroup = "rbac.authorization.k8s.io";
            kind = "Role";
            inherit name;
          };
          subjects = [
            {
              apiGroup = "rbac.authorization.k8s.io";
              kind = "User";
              inherit name;
            }
          ];
        };

        kube-addon-manager-cluster-lister-cr = {
          apiVersion = "rbac.authorization.k8s.io/v1";
          kind = "ClusterRole";
          metadata = {
            name = "${name}:cluster-lister";
          };
          rules = [
            {
              apiGroups = [ "*" ];
              resources = [ "*" ];
              verbs = [ "list" ];
            }
          ];
        };

        kube-addon-manager-cluster-lister-crb = {
          apiVersion = "rbac.authorization.k8s.io/v1";
          kind = "ClusterRoleBinding";
          metadata = {
            name = "${name}:cluster-lister";
          };
          roleRef = {
            apiGroup = "rbac.authorization.k8s.io";
            kind = "ClusterRole";
            name = "${name}:cluster-lister";
          };
          subjects = [
            {
              kind = "User";
              inherit name;
            }
          ];
        };
      }
    );

    services.kubernetes.pki.certs = {
      addonManager = top.lib.mkCert {
        name = "kube-addon-manager";
        CN = "system:kube-addon-manager";
        action = "systemctl restart kube-addon-manager.service";
      };
    };
  };

  meta.buildDocsInSandbox = false;
}

```

`kubernetes/addons/dns.nix`:

```nix
{
  config,
  options,
  pkgs,
  lib,
  ...
}:
let
  version = "1.10.1";
  cfg = config.services.kubernetes.addons.dns;
  ports = {
    dns = 10053;
    health = 10054;
    metrics = 10055;
  };
in
{
  options.services.kubernetes.addons.dns = {
    enable = lib.mkEnableOption "kubernetes dns addon";

    clusterIp = lib.mkOption {
      description = "Dns addon clusterIP";

      # this default is also what kubernetes users
      default =
        (lib.concatStringsSep "." (
          lib.take 3 (lib.splitString "." config.services.kubernetes.apiserver.serviceClusterIpRange)
        ))
        + ".254";
      defaultText = lib.literalMD ''
        The `x.y.z.254` IP of
        `config.${options.services.kubernetes.apiserver.serviceClusterIpRange}`.
      '';
      type = lib.types.str;
    };

    clusterDomain = lib.mkOption {
      description = "Dns cluster domain";
      default = "cluster.local";
      type = lib.types.str;
    };

    replicas = lib.mkOption {
      description = "Number of DNS pod replicas to deploy in the cluster.";
      default = 2;
      type = lib.types.int;
    };

    reconcileMode = lib.mkOption {
      description = ''
        Controls the addon manager reconciliation mode for the DNS addon.

        Setting reconcile mode to EnsureExists makes it possible to tailor DNS behavior by editing the coredns ConfigMap.

        See: <https://github.com/kubernetes/kubernetes/blob/master/cluster/addons/addon-manager/README.md>.
      '';
      default = "Reconcile";
      type = lib.types.enum [
        "Reconcile"
        "EnsureExists"
      ];
    };

    coredns = lib.mkOption {
      description = "Docker image to seed for the CoreDNS container.";
      type = lib.types.attrs;
      default = {
        imageName = "coredns/coredns";
        imageDigest = "sha256:a0ead06651cf580044aeb0a0feba63591858fb2e43ade8c9dea45a6a89ae7e5e";
        finalImageTag = version;
        sha256 = "0wg696920smmal7552a2zdhfncndn5kfammfa8bk8l7dz9bhk0y1";
      };
    };

    corefile = lib.mkOption {
      description = ''
        Custom coredns corefile configuration.

        See: <https://coredns.io/manual/toc/#configuration>.
      '';
      type = lib.types.str;
      default = ''
        .:${toString ports.dns} {
          errors
          health :${toString ports.health}
          kubernetes ${cfg.clusterDomain} in-addr.arpa ip6.arpa {
            pods insecure
            fallthrough in-addr.arpa ip6.arpa
          }
          prometheus :${toString ports.metrics}
          forward . /etc/resolv.conf
          cache 30
          loop
          reload
          loadbalance
        }'';
      defaultText = lib.literalExpression ''
        '''
          .:${toString ports.dns} {
            errors
            health :${toString ports.health}
            kubernetes ''${config.services.kubernetes.addons.dns.clusterDomain} in-addr.arpa ip6.arpa {
              pods insecure
              fallthrough in-addr.arpa ip6.arpa
            }
            prometheus :${toString ports.metrics}
            forward . /etc/resolv.conf
            cache 30
            loop
            reload
            loadbalance
          }
        '''
      '';
    };
  };

  config = lib.mkIf cfg.enable {
    services.kubernetes.kubelet.seedDockerImages = lib.singleton (
      pkgs.dockerTools.pullImage cfg.coredns
    );

    services.kubernetes.addonManager.bootstrapAddons = {
      coredns-cr = {
        apiVersion = "rbac.authorization.k8s.io/v1";
        kind = "ClusterRole";
        metadata = {
          labels = {
            "addonmanager.kubernetes.io/mode" = "Reconcile";
            k8s-app = "kube-dns";
            "kubernetes.io/cluster-service" = "true";
            "kubernetes.io/bootstrapping" = "rbac-defaults";
          };
          name = "system:coredns";
        };
        rules = [
          {
            apiGroups = [ "" ];
            resources = [
              "endpoints"
              "services"
              "pods"
              "namespaces"
            ];
            verbs = [
              "list"
              "watch"
            ];
          }
          {
            apiGroups = [ "" ];
            resources = [ "nodes" ];
            verbs = [ "get" ];
          }
          {
            apiGroups = [ "discovery.k8s.io" ];
            resources = [ "endpointslices" ];
            verbs = [
              "list"
              "watch"
            ];
          }
        ];
      };

      coredns-crb = {
        apiVersion = "rbac.authorization.k8s.io/v1";
        kind = "ClusterRoleBinding";
        metadata = {
          annotations = {
            "rbac.authorization.kubernetes.io/autoupdate" = "true";
          };
          labels = {
            "addonmanager.kubernetes.io/mode" = "Reconcile";
            k8s-app = "kube-dns";
            "kubernetes.io/cluster-service" = "true";
            "kubernetes.io/bootstrapping" = "rbac-defaults";
          };
          name = "system:coredns";
        };
        roleRef = {
          apiGroup = "rbac.authorization.k8s.io";
          kind = "ClusterRole";
          name = "system:coredns";
        };
        subjects = [
          {
            kind = "ServiceAccount";
            name = "coredns";
            namespace = "kube-system";
          }
        ];
      };
    };

    services.kubernetes.addonManager.addons = {
      coredns-sa = {
        apiVersion = "v1";
        kind = "ServiceAccount";
        metadata = {
          labels = {
            "addonmanager.kubernetes.io/mode" = "Reconcile";
            k8s-app = "kube-dns";
            "kubernetes.io/cluster-service" = "true";
          };
          name = "coredns";
          namespace = "kube-system";
        };
      };

      coredns-cm = {
        apiVersion = "v1";
        kind = "ConfigMap";
        metadata = {
          labels = {
            "addonmanager.kubernetes.io/mode" = cfg.reconcileMode;
            k8s-app = "kube-dns";
            "kubernetes.io/cluster-service" = "true";
          };
          name = "coredns";
          namespace = "kube-system";
        };
        data = {
          Corefile = cfg.corefile;
        };
      };

      coredns-deploy = {
        apiVersion = "apps/v1";
        kind = "Deployment";
        metadata = {
          labels = {
            "addonmanager.kubernetes.io/mode" = cfg.reconcileMode;
            k8s-app = "kube-dns";
            "kubernetes.io/cluster-service" = "true";
            "kubernetes.io/name" = "CoreDNS";
          };
          name = "coredns";
          namespace = "kube-system";
        };
        spec = {
          replicas = cfg.replicas;
          selector = {
            matchLabels = {
              k8s-app = "kube-dns";
            };
          };
          strategy = {
            rollingUpdate = {
              maxUnavailable = 1;
            };
            type = "RollingUpdate";
          };
          template = {
            metadata = {
              labels = {
                k8s-app = "kube-dns";
              };
            };
            spec = {
              containers = [
                {
                  args = [
                    "-conf"
                    "/etc/coredns/Corefile"
                  ];
                  image = with cfg.coredns; "${imageName}:${finalImageTag}";
                  imagePullPolicy = "Never";
                  livenessProbe = {
                    failureThreshold = 5;
                    httpGet = {
                      path = "/health";
                      port = ports.health;
                      scheme = "HTTP";
                    };
                    initialDelaySeconds = 60;
                    successThreshold = 1;
                    timeoutSeconds = 5;
                  };
                  name = "coredns";
                  ports = [
                    {
                      containerPort = ports.dns;
                      name = "dns";
                      protocol = "UDP";
                    }
                    {
                      containerPort = ports.dns;
                      name = "dns-tcp";
                      protocol = "TCP";
                    }
                    {
                      containerPort = ports.metrics;
                      name = "metrics";
                      protocol = "TCP";
                    }
                  ];
                  resources = {
                    limits = {
                      memory = "170Mi";
                    };
                    requests = {
                      cpu = "100m";
                      memory = "70Mi";
                    };
                  };
                  securityContext = {
                    allowPrivilegeEscalation = false;
                    capabilities = {
                      drop = [ "all" ];
                    };
                    readOnlyRootFilesystem = true;
                  };
                  volumeMounts = [
                    {
                      mountPath = "/etc/coredns";
                      name = "config-volume";
                      readOnly = true;
                    }
                  ];
                }
              ];
              dnsPolicy = "Default";
              nodeSelector = {
                "beta.kubernetes.io/os" = "linux";
              };
              serviceAccountName = "coredns";
              tolerations = [
                {
                  effect = "NoSchedule";
                  key = "node-role.kubernetes.io/master";
                }
                {
                  key = "CriticalAddonsOnly";
                  operator = "Exists";
                }
              ];
              volumes = [
                {
                  configMap = {
                    items = [
                      {
                        key = "Corefile";
                        path = "Corefile";
                      }
                    ];
                    name = "coredns";
                  };
                  name = "config-volume";
                }
              ];
            };
          };
        };
      };

      coredns-svc = {
        apiVersion = "v1";
        kind = "Service";
        metadata = {
          annotations = {
            "prometheus.io/port" = toString ports.metrics;
            "prometheus.io/scrape" = "true";
          };
          labels = {
            "addonmanager.kubernetes.io/mode" = "Reconcile";
            k8s-app = "kube-dns";
            "kubernetes.io/cluster-service" = "true";
            "kubernetes.io/name" = "CoreDNS";
          };
          name = "kube-dns";
          namespace = "kube-system";
        };
        spec = {
          clusterIP = cfg.clusterIp;
          ports = [
            {
              name = "dns";
              port = 53;
              targetPort = ports.dns;
              protocol = "UDP";
            }
            {
              name = "dns-tcp";
              port = 53;
              targetPort = ports.dns;
              protocol = "TCP";
            }
          ];
          selector = {
            k8s-app = "kube-dns";
          };
        };
      };
    };

    services.kubernetes.kubelet.clusterDns = lib.mkDefault [ cfg.clusterIp ];
  };

  meta.buildDocsInSandbox = false;
}

```

`kubernetes/apiserver.nix`:

```nix
{
  config,
  lib,
  options,
  pkgs,
  ...
}:
let
  top = config.services.kubernetes;
  otop = options.services.kubernetes;
  cfg = top.apiserver;

  isRBACEnabled = lib.elem "RBAC" cfg.authorizationMode;

  apiserverServiceIP = (
    lib.concatStringsSep "." (lib.take 3 (lib.splitString "." cfg.serviceClusterIpRange)) + ".1"
  );
in
{

  imports = [
    (lib.mkRenamedOptionModule
      [ "services" "kubernetes" "apiserver" "admissionControl" ]
      [ "services" "kubernetes" "apiserver" "enableAdmissionPlugins" ]
    )
    (lib.mkRenamedOptionModule
      [ "services" "kubernetes" "apiserver" "address" ]
      [ "services" "kubernetes" "apiserver" "bindAddress" ]
    )
    (lib.mkRemovedOptionModule [ "services" "kubernetes" "apiserver" "insecureBindAddress" ] "")
    (lib.mkRemovedOptionModule [ "services" "kubernetes" "apiserver" "insecurePort" ] "")
    (lib.mkRemovedOptionModule [ "services" "kubernetes" "apiserver" "publicAddress" ] "")
    (lib.mkRenamedOptionModule
      [ "services" "kubernetes" "etcd" "servers" ]
      [ "services" "kubernetes" "apiserver" "etcd" "servers" ]
    )
    (lib.mkRenamedOptionModule
      [ "services" "kubernetes" "etcd" "keyFile" ]
      [ "services" "kubernetes" "apiserver" "etcd" "keyFile" ]
    )
    (lib.mkRenamedOptionModule
      [ "services" "kubernetes" "etcd" "certFile" ]
      [ "services" "kubernetes" "apiserver" "etcd" "certFile" ]
    )
    (lib.mkRenamedOptionModule
      [ "services" "kubernetes" "etcd" "caFile" ]
      [ "services" "kubernetes" "apiserver" "etcd" "caFile" ]
    )
  ];

  ###### interface
  options.services.kubernetes.apiserver = with lib.types; {

    advertiseAddress = lib.mkOption {
      description = ''
        Kubernetes apiserver IP address on which to advertise the apiserver
        to members of the cluster. This address must be reachable by the rest
        of the cluster.
      '';
      default = null;
      type = nullOr str;
    };

    allowPrivileged = lib.mkOption {
      description = "Whether to allow privileged containers on Kubernetes.";
      default = false;
      type = bool;
    };

    authorizationMode = lib.mkOption {
      description = ''
        Kubernetes apiserver authorization mode (AlwaysAllow/AlwaysDeny/ABAC/Webhook/RBAC/Node). See
        <https://kubernetes.io/docs/reference/access-authn-authz/authorization/>
      '';
      default = [
        "RBAC"
        "Node"
      ]; # Enabling RBAC by default, although kubernetes default is AllowAllow
      type = listOf (enum [
        "AlwaysAllow"
        "AlwaysDeny"
        "ABAC"
        "Webhook"
        "RBAC"
        "Node"
      ]);
    };

    authorizationPolicy = lib.mkOption {
      description = ''
        Kubernetes apiserver authorization policy file. See
        <https://kubernetes.io/docs/reference/access-authn-authz/authorization/>
      '';
      default = [ ];
      type = listOf attrs;
    };

    basicAuthFile = lib.mkOption {
      description = ''
        Kubernetes apiserver basic authentication file. See
        <https://kubernetes.io/docs/reference/access-authn-authz/authentication>
      '';
      default = null;
      type = nullOr path;
    };

    bindAddress = lib.mkOption {
      description = ''
        The IP address on which to listen for the --secure-port port.
        The associated interface(s) must be reachable by the rest
        of the cluster, and by CLI/web clients.
      '';
      default = "0.0.0.0";
      type = str;
    };

    clientCaFile = lib.mkOption {
      description = "Kubernetes apiserver CA file for client auth.";
      default = top.caFile;
      defaultText = lib.literalExpression "config.${otop.caFile}";
      type = nullOr path;
    };

    disableAdmissionPlugins = lib.mkOption {
      description = ''
        Kubernetes admission control plugins to disable. See
        <https://kubernetes.io/docs/admin/admission-controllers/>
      '';
      default = [ ];
      type = listOf str;
    };

    enable = lib.mkEnableOption "Kubernetes apiserver";

    enableAdmissionPlugins = lib.mkOption {
      description = ''
        Kubernetes admission control plugins to enable. See
        <https://kubernetes.io/docs/admin/admission-controllers/>
      '';
      default = [
        "NamespaceLifecycle"
        "LimitRanger"
        "ServiceAccount"
        "ResourceQuota"
        "DefaultStorageClass"
        "DefaultTolerationSeconds"
        "NodeRestriction"
      ];
      example = [
        "NamespaceLifecycle"
        "NamespaceExists"
        "LimitRanger"
        "SecurityContextDeny"
        "ServiceAccount"
        "ResourceQuota"
        "PodSecurityPolicy"
        "NodeRestriction"
        "DefaultStorageClass"
      ];
      type = listOf str;
    };

    etcd = {
      servers = lib.mkOption {
        description = "List of etcd servers.";
        default = [ "http://127.0.0.1:2379" ];
        type = types.listOf types.str;
      };

      keyFile = lib.mkOption {
        description = "Etcd key file.";
        default = null;
        type = types.nullOr types.path;
      };

      certFile = lib.mkOption {
        description = "Etcd cert file.";
        default = null;
        type = types.nullOr types.path;
      };

      caFile = lib.mkOption {
        description = "Etcd ca file.";
        default = top.caFile;
        defaultText = lib.literalExpression "config.${otop.caFile}";
        type = types.nullOr types.path;
      };
    };

    extraOpts = lib.mkOption {
      description = "Kubernetes apiserver extra command line options.";
      default = "";
      type = separatedString " ";
    };

    extraSANs = lib.mkOption {
      description = "Extra x509 Subject Alternative Names to be added to the kubernetes apiserver tls cert.";
      default = [ ];
      type = listOf str;
    };

    featureGates = lib.mkOption {
      description = "Attribute set of feature gates.";
      default = top.featureGates;
      defaultText = lib.literalExpression "config.${otop.featureGates}";
      type = attrsOf bool;
    };

    kubeletClientCaFile = lib.mkOption {
      description = "Path to a cert file for connecting to kubelet.";
      default = top.caFile;
      defaultText = lib.literalExpression "config.${otop.caFile}";
      type = nullOr path;
    };

    kubeletClientCertFile = lib.mkOption {
      description = "Client certificate to use for connections to kubelet.";
      default = null;
      type = nullOr path;
    };

    kubeletClientKeyFile = lib.mkOption {
      description = "Key to use for connections to kubelet.";
      default = null;
      type = nullOr path;
    };

    preferredAddressTypes = lib.mkOption {
      description = "List of the preferred NodeAddressTypes to use for kubelet connections.";
      type = nullOr str;
      default = null;
    };

    proxyClientCertFile = lib.mkOption {
      description = "Client certificate to use for connections to proxy.";
      default = null;
      type = nullOr path;
    };

    proxyClientKeyFile = lib.mkOption {
      description = "Key to use for connections to proxy.";
      default = null;
      type = nullOr path;
    };

    runtimeConfig = lib.mkOption {
      description = ''
        Api runtime configuration. See
        <https://kubernetes.io/docs/tasks/administer-cluster/cluster-management/>
      '';
      default = "authentication.k8s.io/v1beta1=true";
      example = "api/all=false,api/v1=true";
      type = str;
    };

    storageBackend = lib.mkOption {
      description = ''
        Kubernetes apiserver storage backend.
      '';
      default = "etcd3";
      type = enum [
        "etcd2"
        "etcd3"
      ];
    };

    securePort = lib.mkOption {
      description = "Kubernetes apiserver secure port.";
      default = 6443;
      type = int;
    };

    apiAudiences = lib.mkOption {
      description = ''
        Kubernetes apiserver ServiceAccount issuer.
      '';
      default = "api,https://kubernetes.default.svc";
      type = str;
    };

    serviceAccountIssuer = lib.mkOption {
      description = ''
        Kubernetes apiserver ServiceAccount issuer.
      '';
      default = "https://kubernetes.default.svc";
      type = str;
    };

    serviceAccountSigningKeyFile = lib.mkOption {
      description = ''
        Path to the file that contains the current private key of the service
        account token issuer. The issuer will sign issued ID tokens with this
        private key.
      '';
      type = path;
    };

    serviceAccountKeyFile = lib.mkOption {
      description = ''
        File containing PEM-encoded x509 RSA or ECDSA private or public keys,
        used to verify ServiceAccount tokens. The specified file can contain
        multiple keys, and the flag can be specified multiple times with
        different files. If unspecified, --tls-private-key-file is used.
        Must be specified when --service-account-signing-key is provided
      '';
      type = path;
    };

    serviceClusterIpRange = lib.mkOption {
      description = ''
        A CIDR notation IP range from which to assign service cluster IPs.
        This must not overlap with any IP ranges assigned to nodes for pods.
      '';
      default = "10.0.0.0/24";
      type = str;
    };

    tlsCertFile = lib.mkOption {
      description = "Kubernetes apiserver certificate file.";
      default = null;
      type = nullOr path;
    };

    tlsKeyFile = lib.mkOption {
      description = "Kubernetes apiserver private key file.";
      default = null;
      type = nullOr path;
    };

    tokenAuthFile = lib.mkOption {
      description = ''
        Kubernetes apiserver token authentication file. See
        <https://kubernetes.io/docs/reference/access-authn-authz/authentication>
      '';
      default = null;
      type = nullOr path;
    };

    verbosity = lib.mkOption {
      description = ''
        Optional glog verbosity level for logging statements. See
        <https://github.com/kubernetes/community/blob/master/contributors/devel/logging.md>
      '';
      default = null;
      type = nullOr int;
    };

    webhookConfig = lib.mkOption {
      description = ''
        Kubernetes apiserver Webhook config file. It uses the kubeconfig file format.
        See <https://kubernetes.io/docs/reference/access-authn-authz/webhook/>
      '';
      default = null;
      type = nullOr path;
    };

  };

  ###### implementation
  config = lib.mkMerge [

    (lib.mkIf cfg.enable {
      systemd.services.kube-apiserver = {
        description = "Kubernetes APIServer Service";
        wantedBy = [ "kubernetes.target" ];
        after = [ "network.target" ];
        serviceConfig = {
          Slice = "kubernetes.slice";
          ExecStart = ''
            ${top.package}/bin/kube-apiserver \
            --allow-privileged=${lib.boolToString cfg.allowPrivileged} \
            --authorization-mode=${lib.concatStringsSep "," cfg.authorizationMode} \
              ${lib.optionalString (lib.elem "ABAC" cfg.authorizationMode) "--authorization-policy-file=${pkgs.writeText "kube-auth-policy.jsonl" (lib.concatMapStringsSep "\n" (l: builtins.toJSON l) cfg.authorizationPolicy)}"} \
              ${lib.optionalString (lib.elem "Webhook" cfg.authorizationMode) "--authorization-webhook-config-file=${cfg.webhookConfig}"} \
            --bind-address=${cfg.bindAddress} \
            ${lib.optionalString (cfg.advertiseAddress != null) "--advertise-address=${cfg.advertiseAddress}"} \
            ${lib.optionalString (cfg.clientCaFile != null) "--client-ca-file=${cfg.clientCaFile}"} \
            --disable-admission-plugins=${lib.concatStringsSep "," cfg.disableAdmissionPlugins} \
            --enable-admission-plugins=${lib.concatStringsSep "," cfg.enableAdmissionPlugins} \
            --etcd-servers=${lib.concatStringsSep "," cfg.etcd.servers} \
            ${lib.optionalString (cfg.etcd.caFile != null) "--etcd-cafile=${cfg.etcd.caFile}"} \
            ${lib.optionalString (cfg.etcd.certFile != null) "--etcd-certfile=${cfg.etcd.certFile}"} \
            ${lib.optionalString (cfg.etcd.keyFile != null) "--etcd-keyfile=${cfg.etcd.keyFile}"} \
            ${
              lib.optionalString (cfg.featureGates != { })
                "--feature-gates=${
                  (lib.concatStringsSep "," (
                    builtins.attrValues (lib.mapAttrs (n: v: "${n}=${lib.trivial.boolToString v}") cfg.featureGates)
                  ))
                }"
            } \
            ${lib.optionalString (cfg.basicAuthFile != null) "--basic-auth-file=${cfg.basicAuthFile}"} \
            ${
              lib.optionalString (
                cfg.kubeletClientCaFile != null
              ) "--kubelet-certificate-authority=${cfg.kubeletClientCaFile}"
            } \
            ${
              lib.optionalString (
                cfg.kubeletClientCertFile != null
              ) "--kubelet-client-certificate=${cfg.kubeletClientCertFile}"
            } \
            ${
              lib.optionalString (
                cfg.kubeletClientKeyFile != null
              ) "--kubelet-client-key=${cfg.kubeletClientKeyFile}"
            } \
            ${
              lib.optionalString (
                cfg.preferredAddressTypes != null
              ) "--kubelet-preferred-address-types=${cfg.preferredAddressTypes}"
            } \
            ${
              lib.optionalString (
                cfg.proxyClientCertFile != null
              ) "--proxy-client-cert-file=${cfg.proxyClientCertFile}"
            } \
            ${
              lib.optionalString (
                cfg.proxyClientKeyFile != null
              ) "--proxy-client-key-file=${cfg.proxyClientKeyFile}"
            } \
            ${lib.optionalString (cfg.runtimeConfig != "") "--runtime-config=${cfg.runtimeConfig}"} \
            --secure-port=${toString cfg.securePort} \
            --api-audiences=${toString cfg.apiAudiences} \
            --service-account-issuer=${toString cfg.serviceAccountIssuer} \
            --service-account-signing-key-file=${cfg.serviceAccountSigningKeyFile} \
            --service-account-key-file=${cfg.serviceAccountKeyFile} \
            --service-cluster-ip-range=${cfg.serviceClusterIpRange} \
            --storage-backend=${cfg.storageBackend} \
            ${lib.optionalString (cfg.tlsCertFile != null) "--tls-cert-file=${cfg.tlsCertFile}"} \
            ${lib.optionalString (cfg.tlsKeyFile != null) "--tls-private-key-file=${cfg.tlsKeyFile}"} \
            ${lib.optionalString (cfg.tokenAuthFile != null) "--token-auth-file=${cfg.tokenAuthFile}"} \
            ${lib.optionalString (cfg.verbosity != null) "--v=${toString cfg.verbosity}"} \
            ${cfg.extraOpts}
          '';
          WorkingDirectory = top.dataDir;
          User = "kubernetes";
          Group = "kubernetes";
          AmbientCapabilities = "cap_net_bind_service";
          Restart = "on-failure";
          RestartSec = 5;
        };

        unitConfig = {
          StartLimitIntervalSec = 0;
        };
      };

      services.etcd = {
        clientCertAuth = lib.mkDefault true;
        peerClientCertAuth = lib.mkDefault true;
        listenClientUrls = lib.mkDefault [ "https://0.0.0.0:2379" ];
        listenPeerUrls = lib.mkDefault [ "https://0.0.0.0:2380" ];
        advertiseClientUrls = lib.mkDefault [ "https://${top.masterAddress}:2379" ];
        initialCluster = lib.mkDefault [ "${top.masterAddress}=https://${top.masterAddress}:2380" ];
        name = lib.mkDefault top.masterAddress;
        initialAdvertisePeerUrls = lib.mkDefault [ "https://${top.masterAddress}:2380" ];
      };

      services.kubernetes.addonManager.bootstrapAddons = lib.mkIf isRBACEnabled {

        apiserver-kubelet-api-admin-crb = {
          apiVersion = "rbac.authorization.k8s.io/v1";
          kind = "ClusterRoleBinding";
          metadata = {
            name = "system:kube-apiserver:kubelet-api-admin";
          };
          roleRef = {
            apiGroup = "rbac.authorization.k8s.io";
            kind = "ClusterRole";
            name = "system:kubelet-api-admin";
          };
          subjects = [
            {
              kind = "User";
              name = "system:kube-apiserver";
            }
          ];
        };

      };

      services.kubernetes.pki.certs = with top.lib; {
        apiServer = mkCert {
          name = "kube-apiserver";
          CN = "kubernetes";
          hosts = [
            "kubernetes.default.svc"
            "kubernetes.default.svc.${top.addons.dns.clusterDomain}"
            cfg.advertiseAddress
            top.masterAddress
            apiserverServiceIP
            "127.0.0.1"
          ] ++ cfg.extraSANs;
          action = "systemctl restart kube-apiserver.service";
        };
        apiserverProxyClient = mkCert {
          name = "kube-apiserver-proxy-client";
          CN = "front-proxy-client";
          action = "systemctl restart kube-apiserver.service";
        };
        apiserverKubeletClient = mkCert {
          name = "kube-apiserver-kubelet-client";
          CN = "system:kube-apiserver";
          action = "systemctl restart kube-apiserver.service";
        };
        apiserverEtcdClient = mkCert {
          name = "kube-apiserver-etcd-client";
          CN = "etcd-client";
          action = "systemctl restart kube-apiserver.service";
        };
        clusterAdmin = mkCert {
          name = "cluster-admin";
          CN = "cluster-admin";
          fields = {
            O = "system:masters";
          };
          privateKeyOwner = "root";
        };
        etcd = mkCert {
          name = "etcd";
          CN = top.masterAddress;
          hosts = [
            "etcd.local"
            "etcd.${top.addons.dns.clusterDomain}"
            top.masterAddress
            cfg.advertiseAddress
          ];
          privateKeyOwner = "etcd";
          action = "systemctl restart etcd.service";
        };
      };

    })

  ];

  meta.buildDocsInSandbox = false;
}

```

`kubernetes/controller-manager.nix`:

```nix
{
  config,
  lib,
  options,
  pkgs,
  ...
}:
let
  top = config.services.kubernetes;
  otop = options.services.kubernetes;
  cfg = top.controllerManager;
in
{
  imports = [
    (lib.mkRenamedOptionModule
      [ "services" "kubernetes" "controllerManager" "address" ]
      [ "services" "kubernetes" "controllerManager" "bindAddress" ]
    )
    (lib.mkRemovedOptionModule [ "services" "kubernetes" "controllerManager" "insecurePort" ] "")
  ];

  ###### interface
  options.services.kubernetes.controllerManager = with lib.types; {

    allocateNodeCIDRs = lib.mkOption {
      description = "Whether to automatically allocate CIDR ranges for cluster nodes.";
      default = true;
      type = bool;
    };

    bindAddress = lib.mkOption {
      description = "Kubernetes controller manager listening address.";
      default = "127.0.0.1";
      type = str;
    };

    clusterCidr = lib.mkOption {
      description = "Kubernetes CIDR Range for Pods in cluster.";
      default = top.clusterCidr;
      defaultText = lib.literalExpression "config.${otop.clusterCidr}";
      type = str;
    };

    enable = lib.mkEnableOption "Kubernetes controller manager";

    extraOpts = lib.mkOption {
      description = "Kubernetes controller manager extra command line options.";
      default = "";
      type = separatedString " ";
    };

    featureGates = lib.mkOption {
      description = "Attribute set of feature gates.";
      default = top.featureGates;
      defaultText = lib.literalExpression "config.${otop.featureGates}";
      type = attrsOf bool;
    };

    kubeconfig = top.lib.mkKubeConfigOptions "Kubernetes controller manager";

    leaderElect = lib.mkOption {
      description = "Whether to start leader election before executing main loop.";
      type = bool;
      default = true;
    };

    rootCaFile = lib.mkOption {
      description = ''
        Kubernetes controller manager certificate authority file included in
        service account's token secret.
      '';
      default = top.caFile;
      defaultText = lib.literalExpression "config.${otop.caFile}";
      type = nullOr path;
    };

    securePort = lib.mkOption {
      description = "Kubernetes controller manager secure listening port.";
      default = 10252;
      type = int;
    };

    serviceAccountKeyFile = lib.mkOption {
      description = ''
        Kubernetes controller manager PEM-encoded private RSA key file used to
        sign service account tokens
      '';
      default = null;
      type = nullOr path;
    };

    tlsCertFile = lib.mkOption {
      description = "Kubernetes controller-manager certificate file.";
      default = null;
      type = nullOr path;
    };

    tlsKeyFile = lib.mkOption {
      description = "Kubernetes controller-manager private key file.";
      default = null;
      type = nullOr path;
    };

    verbosity = lib.mkOption {
      description = ''
        Optional glog verbosity level for logging statements. See
        <https://github.com/kubernetes/community/blob/master/contributors/devel/logging.md>
      '';
      default = null;
      type = nullOr int;
    };

  };

  ###### implementation
  config = lib.mkIf cfg.enable {
    systemd.services.kube-controller-manager = {
      description = "Kubernetes Controller Manager Service";
      wantedBy = [ "kubernetes.target" ];
      after = [ "kube-apiserver.service" ];
      serviceConfig = {
        RestartSec = "30s";
        Restart = "on-failure";
        Slice = "kubernetes.slice";
        ExecStart = ''
          ${top.package}/bin/kube-controller-manager \
                    --allocate-node-cidrs=${lib.boolToString cfg.allocateNodeCIDRs} \
                    --bind-address=${cfg.bindAddress} \
                    ${lib.optionalString (cfg.clusterCidr != null) "--cluster-cidr=${cfg.clusterCidr}"} \
                    ${
                      lib.optionalString (cfg.featureGates != { })
                        "--feature-gates=${
                          lib.concatStringsSep "," (
                            builtins.attrValues (lib.mapAttrs (n: v: "${n}=${lib.trivial.boolToString v}") cfg.featureGates)
                          )
                        }"
                    } \
                    --kubeconfig=${top.lib.mkKubeConfig "kube-controller-manager" cfg.kubeconfig} \
                    --leader-elect=${lib.boolToString cfg.leaderElect} \
                    ${lib.optionalString (cfg.rootCaFile != null) "--root-ca-file=${cfg.rootCaFile}"} \
                    --secure-port=${toString cfg.securePort} \
                    ${
                      lib.optionalString (
                        cfg.serviceAccountKeyFile != null
                      ) "--service-account-private-key-file=${cfg.serviceAccountKeyFile}"
                    } \
                    ${lib.optionalString (cfg.tlsCertFile != null) "--tls-cert-file=${cfg.tlsCertFile}"} \
                    ${
                      lib.optionalString (cfg.tlsKeyFile != null) "--tls-private-key-file=${cfg.tlsKeyFile}"
                    } \
                    ${lib.optionalString (lib.elem "RBAC" top.apiserver.authorizationMode) "--use-service-account-credentials"} \
                    ${lib.optionalString (cfg.verbosity != null) "--v=${toString cfg.verbosity}"} \
                    ${cfg.extraOpts}
        '';
        WorkingDirectory = top.dataDir;
        User = "kubernetes";
        Group = "kubernetes";
      };
      unitConfig = {
        StartLimitIntervalSec = 0;
      };
      path = top.path;
    };

    services.kubernetes.pki.certs = with top.lib; {
      controllerManager = mkCert {
        name = "kube-controller-manager";
        CN = "kube-controller-manager";
        action = "systemctl restart kube-controller-manager.service";
      };
      controllerManagerClient = mkCert {
        name = "kube-controller-manager-client";
        CN = "system:kube-controller-manager";
        action = "systemctl restart kube-controller-manager.service";
      };
    };

    services.kubernetes.controllerManager.kubeconfig.server = lib.mkDefault top.apiserverAddress;
  };

  meta.buildDocsInSandbox = false;
}

```

`kubernetes/default.nix`:

```nix
{
  config,
  lib,
  options,
  pkgs,
  ...
}:
let
  cfg = config.services.kubernetes;
  opt = options.services.kubernetes;

  defaultContainerdSettings = {
    version = 2;
    root = "/var/lib/containerd";
    state = "/run/containerd";
    oom_score = 0;

    grpc = {
      address = "/run/containerd/containerd.sock";
    };

    plugins."io.containerd.grpc.v1.cri" = {
      sandbox_image = "pause:latest";

      cni = {
        bin_dir = "/opt/cni/bin";
        max_conf_num = 0;
      };

      containerd.runtimes.runc = {
        runtime_type = "io.containerd.runc.v2";
        options.SystemdCgroup = true;
      };
    };
  };

  mkKubeConfig =
    name: conf:
    pkgs.writeText "${name}-kubeconfig" (
      builtins.toJSON {
        apiVersion = "v1";
        kind = "Config";
        clusters = [
          {
            name = "local";
            cluster.certificate-authority = conf.caFile or cfg.caFile;
            cluster.server = conf.server;
          }
        ];
        users = [
          {
            inherit name;
            user = {
              client-certificate = conf.certFile;
              client-key = conf.keyFile;
            };
          }
        ];
        contexts = [
          {
            context = {
              cluster = "local";
              user = name;
            };
            name = "local";
          }
        ];
        current-context = "local";
      }
    );

  caCert = secret "ca";

  etcdEndpoints = [ "https://${cfg.masterAddress}:2379" ];

  mkCert =
    {
      name,
      CN,
      hosts ? [ ],
      fields ? { },
      action ? "",
      privateKeyOwner ? "kubernetes",
      privateKeyGroup ? "kubernetes",
    }:
    rec {
      inherit
        name
        caCert
        CN
        hosts
        fields
        action
        ;
      cert = secret name;
      key = secret "${name}-key";
      privateKeyOptions = {
        owner = privateKeyOwner;
        group = privateKeyGroup;
        mode = "0600";
        path = key;
      };
    };

  secret = name: "${cfg.secretsPath}/${name}.pem";

  mkKubeConfigOptions = prefix: {
    server = lib.mkOption {
      description = "${prefix} kube-apiserver server address.";
      type = lib.types.str;
    };

    caFile = lib.mkOption {
      description = "${prefix} certificate authority file used to connect to kube-apiserver.";
      type = lib.types.nullOr lib.types.path;
      default = cfg.caFile;
      defaultText = lib.literalExpression "config.${opt.caFile}";
    };

    certFile = lib.mkOption {
      description = "${prefix} client certificate file used to connect to kube-apiserver.";
      type = lib.types.nullOr lib.types.path;
      default = null;
    };

    keyFile = lib.mkOption {
      description = "${prefix} client key file used to connect to kube-apiserver.";
      type = lib.types.nullOr lib.types.path;
      default = null;
    };
  };
in
{

  imports = [
    (lib.mkRemovedOptionModule [
      "services"
      "kubernetes"
      "addons"
      "dashboard"
    ] "Removed due to it being an outdated version")
    (lib.mkRemovedOptionModule [ "services" "kubernetes" "verbose" ] "")
  ];

  ###### interface

  options.services.kubernetes = {
    roles = lib.mkOption {
      description = ''
        Kubernetes role that this machine should take.

        Master role will enable etcd, apiserver, scheduler, controller manager
        addon manager, flannel and proxy services.
        Node role will enable flannel, docker, kubelet and proxy services.
      '';
      default = [ ];
      type = lib.types.listOf (
        lib.types.enum [
          "master"
          "node"
        ]
      );
    };

    package = lib.mkPackageOption pkgs "kubernetes" { };

    kubeconfig = mkKubeConfigOptions "Default kubeconfig";

    apiserverAddress = lib.mkOption {
      description = ''
        Clusterwide accessible address for the kubernetes apiserver,
        including protocol and optional port.
      '';
      example = "https://kubernetes-apiserver.example.com:6443";
      type = lib.types.str;
    };

    caFile = lib.mkOption {
      description = "Default kubernetes certificate authority";
      type = lib.types.nullOr lib.types.path;
      default = null;
    };

    dataDir = lib.mkOption {
      description = "Kubernetes root directory for managing kubelet files.";
      default = "/var/lib/kubernetes";
      type = lib.types.path;
    };

    easyCerts = lib.mkOption {
      description = "Automatically setup x509 certificates and keys for the entire cluster.";
      default = false;
      type = lib.types.bool;
    };

    featureGates = lib.mkOption {
      description = "List set of feature gates.";
      default = { };
      type = lib.types.attrsOf lib.types.bool;
    };

    masterAddress = lib.mkOption {
      description = "Clusterwide available network address or hostname for the kubernetes master server.";
      example = "master.example.com";
      type = lib.types.str;
    };

    path = lib.mkOption {
      description = "Packages added to the services' PATH environment variable. Both the bin and sbin subdirectories of each package are added.";
      type = lib.types.listOf lib.types.package;
      default = [ ];
    };

    clusterCidr = lib.mkOption {
      description = "Kubernetes controller manager and proxy CIDR Range for Pods in cluster.";
      default = "10.1.0.0/16";
      type = lib.types.nullOr lib.types.str;
    };

    lib = lib.mkOption {
      description = "Common functions for the kubernetes modules.";
      default = {
        inherit mkCert;
        inherit mkKubeConfig;
        inherit mkKubeConfigOptions;
      };
      type = lib.types.attrs;
    };

    secretsPath = lib.mkOption {
      description = "Default location for kubernetes secrets. Not a store location.";
      type = lib.types.path;
      default = cfg.dataDir + "/secrets";
      defaultText = lib.literalExpression ''
        config.${opt.dataDir} + "/secrets"
      '';
    };
  };

  ###### implementation

  config = lib.mkMerge [

    (lib.mkIf cfg.easyCerts {
      services.kubernetes.pki.enable = lib.mkDefault true;
      services.kubernetes.caFile = caCert;
    })

    (lib.mkIf (lib.elem "master" cfg.roles) {
      services.kubernetes.apiserver.enable = lib.mkDefault true;
      services.kubernetes.scheduler.enable = lib.mkDefault true;
      services.kubernetes.controllerManager.enable = lib.mkDefault true;
      services.kubernetes.addonManager.enable = lib.mkDefault true;
      services.kubernetes.proxy.enable = lib.mkDefault true;
      services.etcd.enable = true; # Cannot mkDefault because of flannel default options
      services.kubernetes.kubelet = {
        enable = lib.mkDefault true;
        taints = lib.mkIf (!(lib.elem "node" cfg.roles)) {
          master = {
            key = "node-role.kubernetes.io/master";
            value = "true";
            effect = "NoSchedule";
          };
        };
      };
    })

    (lib.mkIf (lib.all (el: el == "master") cfg.roles) {
      # if this node is only a master make it unschedulable by default
      services.kubernetes.kubelet.unschedulable = lib.mkDefault true;
    })

    (lib.mkIf (lib.elem "node" cfg.roles) {
      services.kubernetes.kubelet.enable = lib.mkDefault true;
      services.kubernetes.proxy.enable = lib.mkDefault true;
    })

    # Using "services.kubernetes.roles" will automatically enable easyCerts and flannel
    (lib.mkIf (cfg.roles != [ ]) {
      services.kubernetes.flannel.enable = lib.mkDefault true;
      services.flannel.etcd.endpoints = lib.mkDefault etcdEndpoints;
      services.kubernetes.easyCerts = lib.mkDefault true;
    })

    (lib.mkIf cfg.apiserver.enable {
      services.kubernetes.pki.etcClusterAdminKubeconfig = lib.mkDefault "kubernetes/cluster-admin.kubeconfig";
      services.kubernetes.apiserver.etcd.servers = lib.mkDefault etcdEndpoints;
    })

    (lib.mkIf cfg.kubelet.enable {
      virtualisation.containerd = {
        enable = lib.mkDefault true;
        settings = lib.mapAttrsRecursive (name: lib.mkDefault) defaultContainerdSettings;
      };
    })

    (lib.mkIf (cfg.apiserver.enable || cfg.controllerManager.enable) {
      services.kubernetes.pki.certs = {
        serviceAccount = mkCert {
          name = "service-account";
          CN = "system:service-account-signer";
          action = ''
            systemctl restart \
              kube-apiserver.service \
              kube-controller-manager.service
          '';
        };
      };
    })

    (lib.mkIf
      (
        cfg.apiserver.enable
        || cfg.scheduler.enable
        || cfg.controllerManager.enable
        || cfg.kubelet.enable
        || cfg.proxy.enable
        || cfg.addonManager.enable
      )
      {
        systemd.targets.kubernetes = {
          description = "Kubernetes";
          wantedBy = [ "multi-user.target" ];
        };

        systemd.tmpfiles.rules = [
          "d /opt/cni/bin 0755 root root -"
          "d /run/kubernetes 0755 kubernetes kubernetes -"
          "d ${cfg.dataDir} 0755 kubernetes kubernetes -"
        ];

        users.users.kubernetes = {
          uid = config.ids.uids.kubernetes;
          description = "Kubernetes user";
          group = "kubernetes";
          home = cfg.dataDir;
          createHome = true;
          homeMode = "755";
        };
        users.groups.kubernetes.gid = config.ids.gids.kubernetes;

        # dns addon is enabled by default
        services.kubernetes.addons.dns.enable = lib.mkDefault true;

        services.kubernetes.apiserverAddress = lib.mkDefault (
          "https://${
            if cfg.apiserver.advertiseAddress != null then
              cfg.apiserver.advertiseAddress
            else
              "${cfg.masterAddress}:${toString cfg.apiserver.securePort}"
          }"
        );
      }
    )
  ];

  meta.buildDocsInSandbox = false;
}

```

`kubernetes/flannel.nix`:

```nix
{
  config,
  lib,
  pkgs,
  ...
}:
let
  top = config.services.kubernetes;
  cfg = top.flannel;

  # we want flannel to use kubernetes itself as configuration backend, not direct etcd
  storageBackend = "kubernetes";
in
{
  ###### interface
  options.services.kubernetes.flannel = {
    enable = lib.mkEnableOption "flannel networking";

    openFirewallPorts = lib.mkOption {
      description = ''Whether to open the Flannel UDP ports in the firewall on all interfaces.'';
      type = lib.types.bool;
      default = true;
    };
  };

  ###### implementation
  config = lib.mkIf cfg.enable {
    services.flannel = {

      enable = lib.mkDefault true;
      network = lib.mkDefault top.clusterCidr;
      inherit storageBackend;
      nodeName = config.services.kubernetes.kubelet.hostname;
    };

    services.kubernetes.kubelet = {
      cni.config = lib.mkDefault [
        {
          name = "mynet";
          type = "flannel";
          cniVersion = "0.3.1";
          delegate = {
            isDefaultGateway = true;
            bridge = "mynet";
          };
        }
      ];
    };

    networking = {
      firewall.allowedUDPPorts = lib.mkIf cfg.openFirewallPorts [
        8285 # flannel udp
        8472 # flannel vxlan
      ];
      dhcpcd.denyInterfaces = [
        "mynet*"
        "flannel*"
      ];
    };

    services.kubernetes.pki.certs = {
      flannelClient = top.lib.mkCert {
        name = "flannel-client";
        CN = "flannel-client";
        action = "systemctl restart flannel.service";
      };
    };

    # give flannel some kubernetes rbac permissions if applicable
    services.kubernetes.addonManager.bootstrapAddons =
      lib.mkIf ((storageBackend == "kubernetes") && (lib.elem "RBAC" top.apiserver.authorizationMode))
        {

          flannel-cr = {
            apiVersion = "rbac.authorization.k8s.io/v1";
            kind = "ClusterRole";
            metadata = {
              name = "flannel";
            };
            rules = [
              {
                apiGroups = [ "" ];
                resources = [ "pods" ];
                verbs = [ "get" ];
              }
              {
                apiGroups = [ "" ];
                resources = [ "nodes" ];
                verbs = [
                  "list"
                  "watch"
                ];
              }
              {
                apiGroups = [ "" ];
                resources = [ "nodes/status" ];
                verbs = [ "patch" ];
              }
            ];
          };

          flannel-crb = {
            apiVersion = "rbac.authorization.k8s.io/v1";
            kind = "ClusterRoleBinding";
            metadata = {
              name = "flannel";
            };
            roleRef = {
              apiGroup = "rbac.authorization.k8s.io";
              kind = "ClusterRole";
              name = "flannel";
            };
            subjects = [
              {
                kind = "User";
                name = "flannel-client";
              }
            ];
          };

        };
  };

  meta.buildDocsInSandbox = false;
}

```

`kubernetes/kubelet.nix`:

```nix
{
  config,
  lib,
  options,
  pkgs,
  ...
}:

with lib;

let
  top = config.services.kubernetes;
  otop = options.services.kubernetes;
  cfg = top.kubelet;

  cniConfig =
    if cfg.cni.config != [ ] && cfg.cni.configDir != null then
      throw "Verbatim CNI-config and CNI configDir cannot both be set."
    else if cfg.cni.configDir != null then
      cfg.cni.configDir
    else
      (pkgs.buildEnv {
        name = "kubernetes-cni-config";
        paths = imap (
          i: entry: pkgs.writeTextDir "${toString (10 + i)}-${entry.type}.conf" (builtins.toJSON entry)
        ) cfg.cni.config;
      });

  infraContainer = pkgs.dockerTools.buildImage {
    name = "pause";
    tag = "latest";
    copyToRoot = pkgs.buildEnv {
      name = "image-root";
      pathsToLink = [ "/bin" ];
      paths = [ top.package.pause ];
    };
    config.Cmd = [ "/bin/pause" ];
  };

  kubeconfig = top.lib.mkKubeConfig "kubelet" cfg.kubeconfig;

  # Flag based settings are deprecated, use the `--config` flag with a
  # `KubeletConfiguration` struct.
  # https://kubernetes.io/docs/tasks/administer-cluster/kubelet-config-file/
  #
  # NOTE: registerWithTaints requires a []core/v1.Taint, therefore requires
  # additional work to be put in config format.
  #
  kubeletConfig = pkgs.writeText "kubelet-config" (
    builtins.toJSON (
      {
        apiVersion = "kubelet.config.k8s.io/v1beta1";
        kind = "KubeletConfiguration";
        address = cfg.address;
        port = cfg.port;
        authentication = {
          x509 = lib.optionalAttrs (cfg.clientCaFile != null) { clientCAFile = cfg.clientCaFile; };
          webhook = {
            enabled = true;
            cacheTTL = "10s";
          };
        };
        authorization = {
          mode = "Webhook";
        };
        cgroupDriver = "systemd";
        hairpinMode = "hairpin-veth";
        registerNode = cfg.registerNode;
        containerRuntimeEndpoint = cfg.containerRuntimeEndpoint;
        healthzPort = cfg.healthz.port;
        healthzBindAddress = cfg.healthz.bind;
      }
      // lib.optionalAttrs (cfg.tlsCertFile != null) { tlsCertFile = cfg.tlsCertFile; }
      // lib.optionalAttrs (cfg.tlsKeyFile != null) { tlsPrivateKeyFile = cfg.tlsKeyFile; }
      // lib.optionalAttrs (cfg.clusterDomain != "") { clusterDomain = cfg.clusterDomain; }
      // lib.optionalAttrs (cfg.clusterDns != [ ]) { clusterDNS = cfg.clusterDns; }
      // lib.optionalAttrs (cfg.featureGates != { }) { featureGates = cfg.featureGates; }
      // lib.optionalAttrs (cfg.extraConfig != { }) cfg.extraConfig
    )
  );

  manifestPath = "kubernetes/manifests";

  taintOptions =
    with lib.types;
    { name, ... }:
    {
      options = {
        key = mkOption {
          description = "Key of taint.";
          default = name;
          defaultText = literalMD "Name of this submodule.";
          type = str;
        };
        value = mkOption {
          description = "Value of taint.";
          type = str;
        };
        effect = mkOption {
          description = "Effect of taint.";
          example = "NoSchedule";
          type = enum [
            "NoSchedule"
            "PreferNoSchedule"
            "NoExecute"
          ];
        };
      };
    };

  taints = concatMapStringsSep "," (v: "${v.key}=${v.value}:${v.effect}") (
    mapAttrsToList (n: v: v) cfg.taints
  );
in
{
  imports = [
    (mkRemovedOptionModule [ "services" "kubernetes" "kubelet" "applyManifests" ] "")
    (mkRemovedOptionModule [ "services" "kubernetes" "kubelet" "cadvisorPort" ] "")
    (mkRemovedOptionModule [ "services" "kubernetes" "kubelet" "allowPrivileged" ] "")
    (mkRemovedOptionModule [ "services" "kubernetes" "kubelet" "networkPlugin" ] "")
    (mkRemovedOptionModule [ "services" "kubernetes" "kubelet" "containerRuntime" ] "")
  ];

  ###### interface
  options.services.kubernetes.kubelet = with lib.types; {

    address = mkOption {
      description = "Kubernetes kubelet info server listening address.";
      default = "0.0.0.0";
      type = str;
    };

    clusterDns = mkOption {
      description = "Use alternative DNS.";
      default = [ "10.1.0.1" ];
      type = listOf str;
    };

    clusterDomain = mkOption {
      description = "Use alternative domain.";
      default = config.services.kubernetes.addons.dns.clusterDomain;
      defaultText = literalExpression "config.${options.services.kubernetes.addons.dns.clusterDomain}";
      type = str;
    };

    clientCaFile = mkOption {
      description = "Kubernetes apiserver CA file for client authentication.";
      default = top.caFile;
      defaultText = literalExpression "config.${otop.caFile}";
      type = nullOr path;
    };

    cni = {
      packages = mkOption {
        description = "List of network plugin packages to install.";
        type = listOf package;
        default = [ ];
      };

      config = mkOption {
        description = "Kubernetes CNI configuration.";
        type = listOf attrs;
        default = [ ];
        example = literalExpression ''
          [{
            "cniVersion": "0.3.1",
            "name": "mynet",
            "type": "bridge",
            "bridge": "cni0",
            "isGateway": true,
            "ipMasq": true,
            "ipam": {
                "type": "host-local",
                "subnet": "10.22.0.0/16",
                "routes": [
                    { "dst": "0.0.0.0/0" }
                ]
            }
          } {
            "cniVersion": "0.3.1",
            "type": "loopback"
          }]
        '';
      };

      configDir = mkOption {
        description = "Path to Kubernetes CNI configuration directory.";
        type = nullOr path;
        default = null;
      };
    };

    containerRuntimeEndpoint = mkOption {
      description = "Endpoint at which to find the container runtime api interface/socket";
      type = str;
      default = "unix:///run/containerd/containerd.sock";
    };

    enable = mkEnableOption "Kubernetes kubelet";

    extraOpts = mkOption {
      description = "Kubernetes kubelet extra command line options.";
      default = "";
      type = separatedString " ";
    };

    extraConfig = mkOption {
      description = ''
        Kubernetes kubelet extra configuration file entries.

        See also [Set Kubelet Parameters Via A Configuration File](https://kubernetes.io/docs/tasks/administer-cluster/kubelet-config-file/)
        and [Kubelet Configuration](https://kubernetes.io/docs/reference/config-api/kubelet-config.v1beta1/).
      '';
      default = { };
      type = attrsOf ((pkgs.formats.json { }).type);
    };

    featureGates = mkOption {
      description = "Attribute set of feature gate";
      default = top.featureGates;
      defaultText = literalExpression "config.${otop.featureGates}";
      type = attrsOf bool;
    };

    healthz = {
      bind = mkOption {
        description = "Kubernetes kubelet healthz listening address.";
        default = "127.0.0.1";
        type = str;
      };

      port = mkOption {
        description = "Kubernetes kubelet healthz port.";
        default = 10248;
        type = port;
      };
    };

    hostname = mkOption {
      description = "Kubernetes kubelet hostname override.";
      defaultText = literalExpression "config.networking.fqdnOrHostName";
      type = str;
    };

    kubeconfig = top.lib.mkKubeConfigOptions "Kubelet";

    manifests = mkOption {
      description = "List of manifests to bootstrap with kubelet (only pods can be created as manifest entry)";
      type = attrsOf attrs;
      default = { };
    };

    nodeIp = mkOption {
      description = "IP address of the node. If set, kubelet will use this IP address for the node.";
      default = null;
      type = nullOr str;
    };

    registerNode = mkOption {
      description = "Whether to auto register kubelet with API server.";
      default = true;
      type = bool;
    };

    port = mkOption {
      description = "Kubernetes kubelet info server listening port.";
      default = 10250;
      type = port;
    };

    seedDockerImages = mkOption {
      description = "List of docker images to preload on system";
      default = [ ];
      type = listOf package;
    };

    taints = mkOption {
      description = "Node taints (https://kubernetes.io/docs/concepts/configuration/assign-pod-node/).";
      default = { };
      type = attrsOf (submodule [ taintOptions ]);
    };

    tlsCertFile = mkOption {
      description = "File containing x509 Certificate for HTTPS.";
      default = null;
      type = nullOr path;
    };

    tlsKeyFile = mkOption {
      description = "File containing x509 private key matching tlsCertFile.";
      default = null;
      type = nullOr path;
    };

    unschedulable = mkOption {
      description = "Whether to set node taint to unschedulable=true as it is the case of node that has only master role.";
      default = false;
      type = bool;
    };

    verbosity = mkOption {
      description = ''
        Optional glog verbosity level for logging statements. See
        <https://github.com/kubernetes/community/blob/master/contributors/devel/logging.md>
      '';
      default = null;
      type = nullOr int;
    };

  };

  ###### implementation
  config = mkMerge [
    (mkIf cfg.enable {

      environment.etc."cni/net.d".source = cniConfig;

      services.kubernetes.kubelet.seedDockerImages = [ infraContainer ];

      boot.kernel.sysctl = {
        "net.bridge.bridge-nf-call-iptables" = 1;
        "net.ipv4.ip_forward" = 1;
        "net.bridge.bridge-nf-call-ip6tables" = 1;
      };

      systemd.services.kubelet = {
        description = "Kubernetes Kubelet Service";
        wantedBy = [ "kubernetes.target" ];
        after = [
          "containerd.service"
          "network.target"
          "kube-apiserver.service"
        ];
        path =
          with pkgs;
          [
            gitMinimal
            openssh
            util-linux
            iproute2
            ethtool
            thin-provisioning-tools
            iptables
            socat
          ]
          ++ lib.optional config.boot.zfs.enabled config.boot.zfs.package
          ++ top.path;
        preStart = ''
          ${concatMapStrings (img: ''
            echo "Seeding container image: ${img}"
            ${
              if (lib.hasSuffix "gz" img) then
                ''${pkgs.gzip}/bin/zcat "${img}" | ${pkgs.containerd}/bin/ctr -n k8s.io image import -''
              else
                ''${pkgs.coreutils}/bin/cat "${img}" | ${pkgs.containerd}/bin/ctr -n k8s.io image import -''
            }
          '') cfg.seedDockerImages}

          rm /opt/cni/bin/* || true
          ${concatMapStrings (package: ''
            echo "Linking cni package: ${package}"
            ln -fs ${package}/bin/* /opt/cni/bin
          '') cfg.cni.packages}
        '';
        serviceConfig = {
          Slice = "kubernetes.slice";
          CPUAccounting = true;
          MemoryAccounting = true;
          Restart = "on-failure";
          RestartSec = "1000ms";
          ExecStart = ''
            ${top.package}/bin/kubelet \
                        --config=${kubeletConfig} \
                        --hostname-override=${cfg.hostname} \
                        --kubeconfig=${kubeconfig} \
                        ${optionalString (cfg.nodeIp != null) "--node-ip=${cfg.nodeIp}"} \
                        --pod-infra-container-image=pause \
                        ${optionalString (cfg.manifests != { }) "--pod-manifest-path=/etc/${manifestPath}"} \
                        ${optionalString (taints != "") "--register-with-taints=${taints}"} \
                        --root-dir=${top.dataDir} \
                        ${optionalString (cfg.verbosity != null) "--v=${toString cfg.verbosity}"} \
                        ${cfg.extraOpts}
          '';
          WorkingDirectory = top.dataDir;
        };
        unitConfig = {
          StartLimitIntervalSec = 0;
        };
      };

      # Always include cni plugins
      services.kubernetes.kubelet.cni.packages = [
        pkgs.cni-plugins
        pkgs.cni-plugin-flannel
      ];

      boot.kernelModules = [
        "br_netfilter"
        "overlay"
      ];

      services.kubernetes.kubelet.hostname = mkDefault (lib.toLower config.networking.fqdnOrHostName);

      services.kubernetes.pki.certs = with top.lib; {
        kubelet = mkCert {
          name = "kubelet";
          CN = top.kubelet.hostname;
          action = "systemctl restart kubelet.service";

        };
        kubeletClient = mkCert {
          name = "kubelet-client";
          CN = "system:node:${top.kubelet.hostname}";
          fields = {
            O = "system:nodes";
          };
          action = "systemctl restart kubelet.service";
        };
      };

      services.kubernetes.kubelet.kubeconfig.server = mkDefault top.apiserverAddress;
    })

    (mkIf (cfg.enable && cfg.manifests != { }) {
      environment.etc = mapAttrs' (
        name: manifest:
        nameValuePair "${manifestPath}/${name}.json" {
          text = builtins.toJSON manifest;
          mode = "0755";
        }
      ) cfg.manifests;
    })

    (mkIf (cfg.unschedulable && cfg.enable) {
      services.kubernetes.kubelet.taints.unschedulable = {
        value = "true";
        effect = "NoSchedule";
      };
    })

  ];

  meta.buildDocsInSandbox = false;
}

```

`kubernetes/pki.nix`:

```nix
{
  config,
  lib,
  pkgs,
  ...
}:

with lib;

let
  top = config.services.kubernetes;
  cfg = top.pki;

  csrCA = pkgs.writeText "kube-pki-cacert-csr.json" (
    builtins.toJSON {
      key = {
        algo = "rsa";
        size = 2048;
      };
      names = singleton cfg.caSpec;
    }
  );

  csrCfssl = pkgs.writeText "kube-pki-cfssl-csr.json" (
    builtins.toJSON {
      key = {
        algo = "rsa";
        size = 2048;
      };
      CN = top.masterAddress;
      hosts = [ top.masterAddress ] ++ cfg.cfsslAPIExtraSANs;
    }
  );

  cfsslAPITokenBaseName = "apitoken.secret";
  cfsslAPITokenPath = "${config.services.cfssl.dataDir}/${cfsslAPITokenBaseName}";
  certmgrAPITokenPath = "${top.secretsPath}/${cfsslAPITokenBaseName}";
  cfsslAPITokenLength = 32;

  clusterAdminKubeconfig =
    with cfg.certs.clusterAdmin;
    top.lib.mkKubeConfig "cluster-admin" {
      server = top.apiserverAddress;
      certFile = cert;
      keyFile = key;
    };

  remote = with config.services; "https://${kubernetes.masterAddress}:${toString cfssl.port}";
in
{
  ###### interface
  options.services.kubernetes.pki = with lib.types; {

    enable = mkEnableOption "easyCert issuer service";

    certs = mkOption {
      description = "List of certificate specs to feed to cert generator.";
      default = { };
      type = attrs;
    };

    genCfsslCACert = mkOption {
      description = ''
        Whether to automatically generate cfssl CA certificate and key,
        if they don't exist.
      '';
      default = true;
      type = bool;
    };

    genCfsslAPICerts = mkOption {
      description = ''
        Whether to automatically generate cfssl API webserver TLS cert and key,
        if they don't exist.
      '';
      default = true;
      type = bool;
    };

    cfsslAPIExtraSANs = mkOption {
      description = ''
        Extra x509 Subject Alternative Names to be added to the cfssl API webserver TLS cert.
      '';
      default = [ ];
      example = [ "subdomain.example.com" ];
      type = listOf str;
    };

    genCfsslAPIToken = mkOption {
      description = ''
        Whether to automatically generate cfssl API-token secret,
        if they doesn't exist.
      '';
      default = true;
      type = bool;
    };

    pkiTrustOnBootstrap = mkOption {
      description = "Whether to always trust remote cfssl server upon initial PKI bootstrap.";
      default = true;
      type = bool;
    };

    caCertPathPrefix = mkOption {
      description = ''
        Path-prefrix for the CA-certificate to be used for cfssl signing.
        Suffixes ".pem" and "-key.pem" will be automatically appended for
        the public and private keys respectively.
      '';
      default = "${config.services.cfssl.dataDir}/ca";
      defaultText = literalExpression ''"''${config.services.cfssl.dataDir}/ca"'';
      type = str;
    };

    caSpec = mkOption {
      description = "Certificate specification for the auto-generated CAcert.";
      default = {
        CN = "kubernetes-cluster-ca";
        O = "NixOS";
        OU = "services.kubernetes.pki.caSpec";
        L = "auto-generated";
      };
      type = attrs;
    };

    etcClusterAdminKubeconfig = mkOption {
      description = ''
        Symlink a kubeconfig with cluster-admin privileges to environment path
        (/etc/\<path\>).
      '';
      default = null;
      type = nullOr str;
    };

  };

  ###### implementation
  config = mkIf cfg.enable (
    let
      cfsslCertPathPrefix = "${config.services.cfssl.dataDir}/cfssl";
      cfsslCert = "${cfsslCertPathPrefix}.pem";
      cfsslKey = "${cfsslCertPathPrefix}-key.pem";
    in
    {

      services.cfssl = mkIf (top.apiserver.enable) {
        enable = true;
        address = "0.0.0.0";
        tlsCert = cfsslCert;
        tlsKey = cfsslKey;
        configFile = toString (
          pkgs.writeText "cfssl-config.json" (
            builtins.toJSON {
              signing = {
                profiles = {
                  default = {
                    usages = [ "digital signature" ];
                    auth_key = "default";
                    expiry = "720h";
                  };
                };
              };
              auth_keys = {
                default = {
                  type = "standard";
                  key = "file:${cfsslAPITokenPath}";
                };
              };
            }
          )
        );
      };

      systemd.services.cfssl.preStart =
        with pkgs;
        with config.services.cfssl;
        mkIf (top.apiserver.enable) (
          concatStringsSep "\n" [
            "set -e"
            (optionalString cfg.genCfsslCACert ''
              if [ ! -f "${cfg.caCertPathPrefix}.pem" ]; then
                ${cfssl}/bin/cfssl genkey -initca ${csrCA} | \
                  ${cfssl}/bin/cfssljson -bare ${cfg.caCertPathPrefix}
              fi
            '')
            (optionalString cfg.genCfsslAPICerts ''
              if [ ! -f "${dataDir}/cfssl.pem" ]; then
                ${cfssl}/bin/cfssl gencert -ca "${cfg.caCertPathPrefix}.pem" -ca-key "${cfg.caCertPathPrefix}-key.pem" ${csrCfssl} | \
                  ${cfssl}/bin/cfssljson -bare ${cfsslCertPathPrefix}
              fi
            '')
            (optionalString cfg.genCfsslAPIToken ''
              if [ ! -f "${cfsslAPITokenPath}" ]; then
                install -o cfssl -m 400 <(head -c ${
                  toString (cfsslAPITokenLength / 2)
                } /dev/urandom | od -An -t x | tr -d ' ') "${cfsslAPITokenPath}"
              fi
            '')
          ]
        );

      systemd.services.kube-certmgr-bootstrap = {
        description = "Kubernetes certmgr bootstrapper";
        wantedBy = [ "certmgr.service" ];
        after = [ "cfssl.target" ];
        script = concatStringsSep "\n" [
          ''
            set -e

            # If there's a cfssl (cert issuer) running locally, then don't rely on user to
            # manually paste it in place. Just symlink.
            # otherwise, create the target file, ready for users to insert the token

            mkdir -p "$(dirname "${certmgrAPITokenPath}")"
            if [ -f "${cfsslAPITokenPath}" ]; then
              ln -fs "${cfsslAPITokenPath}" "${certmgrAPITokenPath}"
            elif [ ! -f "${certmgrAPITokenPath}" ]; then
              # Don't remove the token if it already exists
              install -m 600 /dev/null "${certmgrAPITokenPath}"
            fi
          ''
          (optionalString (cfg.pkiTrustOnBootstrap) ''
            if [ ! -f "${top.caFile}" ] || [ $(cat "${top.caFile}" | wc -c) -lt 1 ]; then
              ${pkgs.curl}/bin/curl --fail-early -f -kd '{}' ${remote}/api/v1/cfssl/info | \
                ${pkgs.cfssl}/bin/cfssljson -stdout >${top.caFile}
            fi
          '')
        ];
        serviceConfig = {
          RestartSec = "10s";
          Restart = "on-failure";
        };
      };

      services.certmgr = {
        enable = true;
        package = pkgs.certmgr;
        svcManager = "command";
        specs =
          let
            mkSpec = _: cert: {
              inherit (cert) action;
              authority = {
                inherit remote;
                root_ca = cert.caCert;
                profile = "default";
                auth_key_file = certmgrAPITokenPath;
              };
              certificate = {
                path = cert.cert;
              };
              private_key = cert.privateKeyOptions;
              request = {
                hosts = [ cert.CN ] ++ cert.hosts;
                inherit (cert) CN;
                key = {
                  algo = "rsa";
                  size = 2048;
                };
                names = [ cert.fields ];
              };
            };
          in
          mapAttrs mkSpec cfg.certs;
      };

      #TODO: Get rid of kube-addon-manager in the future for the following reasons
      # - it is basically just a shell script wrapped around kubectl
      # - it assumes that it is clusterAdmin or can gain clusterAdmin rights through serviceAccount
      # - it is designed to be used with k8s system components only
      # - it would be better with a more Nix-oriented way of managing addons
      systemd.services.kube-addon-manager = mkIf top.addonManager.enable (mkMerge [
        {
          environment.KUBECONFIG =
            with cfg.certs.addonManager;
            top.lib.mkKubeConfig "addon-manager" {
              server = top.apiserverAddress;
              certFile = cert;
              keyFile = key;
            };
        }

        (optionalAttrs (top.addonManager.bootstrapAddons != { }) {
          serviceConfig.PermissionsStartOnly = true;
          preStart =
            with pkgs;
            let
              files = mapAttrsToList (
                n: v: writeText "${n}.json" (builtins.toJSON v)
              ) top.addonManager.bootstrapAddons;
            in
            ''
              export KUBECONFIG=${clusterAdminKubeconfig}
              ${top.package}/bin/kubectl apply -f ${concatStringsSep " \\\n -f " files}
            '';
        })
      ]);

      environment.etc.${cfg.etcClusterAdminKubeconfig}.source = mkIf (
        cfg.etcClusterAdminKubeconfig != null
      ) clusterAdminKubeconfig;

      environment.systemPackages = mkIf (top.kubelet.enable || top.proxy.enable) [
        (pkgs.writeScriptBin "nixos-kubernetes-node-join" ''
          set -e
          exec 1>&2

          if [ $# -gt 0 ]; then
            echo "Usage: $(basename $0)"
            echo ""
            echo "No args. Apitoken must be provided on stdin."
            echo "To get the apitoken, execute: 'sudo cat ${certmgrAPITokenPath}' on the master node."
            exit 1
          fi

          if [ $(id -u) != 0 ]; then
            echo "Run as root please."
            exit 1
          fi

          read -r token
          if [ ''${#token} != ${toString cfsslAPITokenLength} ]; then
            echo "Token must be of length ${toString cfsslAPITokenLength}."
            exit 1
          fi

          install -m 0600 <(echo $token) ${certmgrAPITokenPath}

          echo "Restarting certmgr..." >&1
          systemctl restart certmgr

          echo "Waiting for certs to appear..." >&1

          ${optionalString top.kubelet.enable ''
            while [ ! -f ${cfg.certs.kubelet.cert} ]; do sleep 1; done
            echo "Restarting kubelet..." >&1
            systemctl restart kubelet
          ''}

          ${optionalString top.proxy.enable ''
            while [ ! -f ${cfg.certs.kubeProxyClient.cert} ]; do sleep 1; done
            echo "Restarting kube-proxy..." >&1
            systemctl restart kube-proxy
          ''}

          ${optionalString top.flannel.enable ''
            while [ ! -f ${cfg.certs.flannelClient.cert} ]; do sleep 1; done
            echo "Restarting flannel..." >&1
            systemctl restart flannel
          ''}

          echo "Node joined successfully"
        '')
      ];

      # isolate etcd on loopback at the master node
      # easyCerts doesn't support multimaster clusters anyway atm.
      services.etcd = with cfg.certs.etcd; {
        listenClientUrls = [ "https://127.0.0.1:2379" ];
        listenPeerUrls = [ "https://127.0.0.1:2380" ];
        advertiseClientUrls = [ "https://etcd.local:2379" ];
        initialCluster = [ "${top.masterAddress}=https://etcd.local:2380" ];
        initialAdvertisePeerUrls = [ "https://etcd.local:2380" ];
        certFile = mkDefault cert;
        keyFile = mkDefault key;
        trustedCaFile = mkDefault caCert;
      };
      networking.extraHosts = mkIf (config.services.etcd.enable) ''
        127.0.0.1 etcd.${top.addons.dns.clusterDomain} etcd.local
      '';

      services.flannel = with cfg.certs.flannelClient; {
        kubeconfig = top.lib.mkKubeConfig "flannel" {
          server = top.apiserverAddress;
          certFile = cert;
          keyFile = key;
        };
      };

      services.kubernetes = {

        apiserver = mkIf top.apiserver.enable (
          with cfg.certs.apiServer;
          {
            etcd = with cfg.certs.apiserverEtcdClient; {
              servers = [ "https://etcd.local:2379" ];
              certFile = mkDefault cert;
              keyFile = mkDefault key;
              caFile = mkDefault caCert;
            };
            clientCaFile = mkDefault caCert;
            tlsCertFile = mkDefault cert;
            tlsKeyFile = mkDefault key;
            serviceAccountKeyFile = mkDefault cfg.certs.serviceAccount.cert;
            serviceAccountSigningKeyFile = mkDefault cfg.certs.serviceAccount.key;
            kubeletClientCaFile = mkDefault caCert;
            kubeletClientCertFile = mkDefault cfg.certs.apiserverKubeletClient.cert;
            kubeletClientKeyFile = mkDefault cfg.certs.apiserverKubeletClient.key;
            proxyClientCertFile = mkDefault cfg.certs.apiserverProxyClient.cert;
            proxyClientKeyFile = mkDefault cfg.certs.apiserverProxyClient.key;
          }
        );
        controllerManager = mkIf top.controllerManager.enable {
          serviceAccountKeyFile = mkDefault cfg.certs.serviceAccount.key;
          rootCaFile = cfg.certs.controllerManagerClient.caCert;
          kubeconfig = with cfg.certs.controllerManagerClient; {
            certFile = mkDefault cert;
            keyFile = mkDefault key;
          };
        };
        scheduler = mkIf top.scheduler.enable {
          kubeconfig = with cfg.certs.schedulerClient; {
            certFile = mkDefault cert;
            keyFile = mkDefault key;
          };
        };
        kubelet = mkIf top.kubelet.enable {
          clientCaFile = mkDefault cfg.certs.kubelet.caCert;
          tlsCertFile = mkDefault cfg.certs.kubelet.cert;
          tlsKeyFile = mkDefault cfg.certs.kubelet.key;
          kubeconfig = with cfg.certs.kubeletClient; {
            certFile = mkDefault cert;
            keyFile = mkDefault key;
          };
        };
        proxy = mkIf top.proxy.enable {
          kubeconfig = with cfg.certs.kubeProxyClient; {
            certFile = mkDefault cert;
            keyFile = mkDefault key;
          };
        };
      };
    }
  );

  meta.buildDocsInSandbox = false;
}

```

`kubernetes/proxy.nix`:

```nix
{
  config,
  lib,
  options,
  pkgs,
  ...
}:

with lib;

let
  top = config.services.kubernetes;
  otop = options.services.kubernetes;
  cfg = top.proxy;
in
{
  imports = [
    (mkRenamedOptionModule
      [ "services" "kubernetes" "proxy" "address" ]
      [ "services" "kubernetes" "proxy" "bindAddress" ]
    )
  ];

  ###### interface
  options.services.kubernetes.proxy = with lib.types; {

    bindAddress = mkOption {
      description = "Kubernetes proxy listening address.";
      default = "0.0.0.0";
      type = str;
    };

    enable = mkEnableOption "Kubernetes proxy";

    extraOpts = mkOption {
      description = "Kubernetes proxy extra command line options.";
      default = "";
      type = separatedString " ";
    };

    featureGates = mkOption {
      description = "Attribute set of feature gates.";
      default = top.featureGates;
      defaultText = literalExpression "config.${otop.featureGates}";
      type = attrsOf bool;
    };

    hostname = mkOption {
      description = "Kubernetes proxy hostname override.";
      default = config.networking.hostName;
      defaultText = literalExpression "config.networking.hostName";
      type = str;
    };

    kubeconfig = top.lib.mkKubeConfigOptions "Kubernetes proxy";

    verbosity = mkOption {
      description = ''
        Optional glog verbosity level for logging statements. See
        <https://github.com/kubernetes/community/blob/master/contributors/devel/logging.md>
      '';
      default = null;
      type = nullOr int;
    };

  };

  ###### implementation
  config = mkIf cfg.enable {
    systemd.services.kube-proxy = {
      description = "Kubernetes Proxy Service";
      wantedBy = [ "kubernetes.target" ];
      after = [ "kube-apiserver.service" ];
      path = with pkgs; [
        iptables
        conntrack-tools
      ];
      serviceConfig = {
        Slice = "kubernetes.slice";
        ExecStart = ''
          ${top.package}/bin/kube-proxy \
          --bind-address=${cfg.bindAddress} \
          ${optionalString (top.clusterCidr != null) "--cluster-cidr=${top.clusterCidr}"} \
          ${
            optionalString (cfg.featureGates != { })
              "--feature-gates=${
                concatStringsSep "," (
                  builtins.attrValues (mapAttrs (n: v: "${n}=${trivial.boolToString v}") cfg.featureGates)
                )
              }"
          } \
          --hostname-override=${cfg.hostname} \
          --kubeconfig=${top.lib.mkKubeConfig "kube-proxy" cfg.kubeconfig} \
          ${optionalString (cfg.verbosity != null) "--v=${toString cfg.verbosity}"} \
          ${cfg.extraOpts}
        '';
        WorkingDirectory = top.dataDir;
        Restart = "on-failure";
        RestartSec = 5;
      };
      unitConfig = {
        StartLimitIntervalSec = 0;
      };
    };

    services.kubernetes.proxy.hostname = with config.networking; mkDefault hostName;

    services.kubernetes.pki.certs = {
      kubeProxyClient = top.lib.mkCert {
        name = "kube-proxy-client";
        CN = "system:kube-proxy";
        action = "systemctl restart kube-proxy.service";
      };
    };

    services.kubernetes.proxy.kubeconfig.server = mkDefault top.apiserverAddress;
  };

  meta.buildDocsInSandbox = false;
}

```

`kubernetes/scheduler.nix`:

```nix
{
  config,
  lib,
  options,
  pkgs,
  ...
}:
let
  top = config.services.kubernetes;
  otop = options.services.kubernetes;
  cfg = top.scheduler;
in
{
  ###### interface
  options.services.kubernetes.scheduler = with lib.types; {

    address = lib.mkOption {
      description = "Kubernetes scheduler listening address.";
      default = "127.0.0.1";
      type = str;
    };

    enable = lib.mkEnableOption "Kubernetes scheduler";

    extraOpts = lib.mkOption {
      description = "Kubernetes scheduler extra command line options.";
      default = "";
      type = separatedString " ";
    };

    featureGates = lib.mkOption {
      description = "Attribute set of feature gates.";
      default = top.featureGates;
      defaultText = lib.literalExpression "config.${otop.featureGates}";
      type = attrsOf bool;
    };

    kubeconfig = top.lib.mkKubeConfigOptions "Kubernetes scheduler";

    leaderElect = lib.mkOption {
      description = "Whether to start leader election before executing main loop.";
      type = bool;
      default = true;
    };

    port = lib.mkOption {
      description = "Kubernetes scheduler listening port.";
      default = 10251;
      type = port;
    };

    verbosity = lib.mkOption {
      description = ''
        Optional glog verbosity level for logging statements. See
        <https://github.com/kubernetes/community/blob/master/contributors/devel/logging.md>
      '';
      default = null;
      type = nullOr int;
    };

  };

  ###### implementation
  config = lib.mkIf cfg.enable {
    systemd.services.kube-scheduler = {
      description = "Kubernetes Scheduler Service";
      wantedBy = [ "kubernetes.target" ];
      after = [ "kube-apiserver.service" ];
      serviceConfig = {
        Slice = "kubernetes.slice";
        ExecStart = ''
          ${top.package}/bin/kube-scheduler \
                    --bind-address=${cfg.address} \
                    ${
                      lib.optionalString (cfg.featureGates != { })
                        "--feature-gates=${
                          lib.concatStringsSep "," (
                            builtins.attrValues (lib.mapAttrs (n: v: "${n}=${lib.trivial.boolToString v}") cfg.featureGates)
                          )
                        }"
                    } \
                    --kubeconfig=${top.lib.mkKubeConfig "kube-scheduler" cfg.kubeconfig} \
                    --leader-elect=${lib.boolToString cfg.leaderElect} \
                    --secure-port=${toString cfg.port} \
                    ${lib.optionalString (cfg.verbosity != null) "--v=${toString cfg.verbosity}"} \
                    ${cfg.extraOpts}
        '';
        WorkingDirectory = top.dataDir;
        User = "kubernetes";
        Group = "kubernetes";
        Restart = "on-failure";
        RestartSec = 5;
      };
      unitConfig = {
        StartLimitIntervalSec = 0;
      };
    };

    services.kubernetes.pki.certs = {
      schedulerClient = top.lib.mkCert {
        name = "kube-scheduler-client";
        CN = "system:kube-scheduler";
        action = "systemctl restart kube-scheduler.service";
      };
    };

    services.kubernetes.scheduler.kubeconfig.server = lib.mkDefault top.apiserverAddress;
  };

  meta.buildDocsInSandbox = false;
}

```
===

mon code nix
===
Project Path: nix

Source Tree:

```txt
nix
├── flake.nix
├── modules
│   └── kubernetes
│       ├── master.nix
│       └── worker.nix
└── vm-config.nix

```

`nix/flake.nix`:

```nix
{
  description = "NixOS Kubernetes VM";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/24.11";
    nixos-generators = {
      url = "github:nix-community/nixos-generators";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, nixos-generators }: {
    packages.x86_64-linux = {
      qcow = nixos-generators.nixosGenerate {
        system = "x86_64-linux";
        modules = [
          ./vm-config.nix
        ];
        format = "qcow";
      };
    };
  };
}
```

`nix/modules/kubernetes/master.nix`:

```nix
{ config, lib, pkgs, ... }:

{

  environment.systemPackages = with pkgs; [
    kubectl
    kompose
    kubernetes
  ];

  services.kubernetes = {
    apiserver.enable = true;
    controllerManager.enable = true;
    scheduler.enable = true;
    addonManager.enable = true;
    proxy.enable = true;
    #flannel.enable = true;
    kubelet.enable = true;
    #easyCerts = true;
    addons.dns.enable = true;
    kubelet.extraOpts = "--fail-swap-on=false";
  };
  #services.kubernetes.masterAddress = "127.0.0.1";
  #services.kubernetes.masterAddress = "192.168.222.22";

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
```

`nix/modules/kubernetes/worker.nix`:

```nix
{ config, lib, pkgs, masterIP ? "192.168.222.22", ... }:

{

  environment.systemPackages = with pkgs; [
    kubectl
  ];

  # Kubernetes Worker Node Configuration
  services.kubernetes = {
    kubelet.enable = true;
    proxy.enable = true;
    flannel.enable = true;
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
```

`nix/vm-config.nix`:

```nix
{ config, pkgs, lib, ... }:

let
  diskSize = 16384; # 16GB in MiB

  baseSystem = { ... }: {
    boot.kernelPackages = pkgs.linuxPackages_6_1;
    boot.loader.systemd-boot.enable = true;
    boot.loader.efi.canTouchEfiVariables = true;

    networking.useDHCP = true;
    networking.useNetworkd = true;
    systemd.network.enable = true;

    nix.settings.experimental-features = [ "nix-command" "flakes" ];
    time.timeZone = "UTC";

    users.users.odancona = {
      isNormalUser = true;
      initialHashedPassword = "$y$j9T$u8873E9Qlnqv13YKSP2NB/$pgKfnnIDxsnoUVr9uXXYRqAdajpKDn5la2UShIw36z."; # Password
      extraGroups = [ "wheel" ];
      openssh.authorizedKeys.keys = [
        (builtins.readFile /home/olivier/.ssh/rhodey.pub)
        (builtins.readFile /home/olivier/.ssh/id_ed25519.pub)
      ];
    };

    services.openssh.enable = true;

    environment.systemPackages = with pkgs; [
      vim
      curl
      tree
      btop
      bat
      fastfetch
      git
      pacman
    ];

    swapDevices = [];
    virtualisation.diskSize = diskSize;
  };

  MasterConfigK8s = import ./modules/kubernetes/master.nix { 
    inherit config lib pkgs;
  };

  WorkerConfigK8s = import ./modules/kubernetes/worker.nix {
    inherit config lib pkgs;
  };

in
{
  imports = [
    (baseSystem { })
    # Uncomment below according to node role
    MasterConfigK8s
    #WorkerConfigK8s
  ];

  system.stateVersion = "24.05";
}
```
===

Comment je dois configurer pour ne pas avoir le masterAddress ?