{
  description = "NixOS Cluster VMs";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/24.11";
    nixos-generators = {
      url = "github:nix-community/nixos-generators";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, nixos-generators }:
  let
    system = "x86_64-linux";
    definitions = {
      k8s-master = [ ./vm-config.nix ./modules/kubernetes/master.nix ];
      k8s-worker = [ ./vm-config.nix ./modules/kubernetes/worker.nix ];
      # slurm-master = [ ./vm-config.nix ./modules/slurm/master.nix ];
      # slurm-worker = [ ./vm-config.nix ./modules/slurm/worker.nix ];
    };
  in
  {
    packages.x86_64-linux =
      nixpkgs.lib.mapAttrs
        (name: modules:
          nixos-generators.nixosGenerate {
            inherit system modules;
            format = "qcow";
            specialArgs = { self = self; };
          }
        )
        definitions;

    nixosConfigurations =
      nixpkgs.lib.mapAttrs
        (name: modules:
          nixpkgs.lib.nixosSystem {
            inherit system modules;
            specialArgs = { self = self; };
          }
        )
        definitions;
  };
}